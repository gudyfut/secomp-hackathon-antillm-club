"""FastAPI transport for the local real-time Campus Sentinel dashboard."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from typesafe_sdk import AsyncTypeSafeClient
from ultralytics import YOLO

from contracts import PerceptionFrame, WorldState
from decision.jev import JevDecisionEngine

from .runtime import DecisionCoordinator, VisionRuntime

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = Path(__file__).resolve().parent / "static"
LOGGER = logging.getLogger(__name__)


def _compute_config(profile: str) -> tuple[str | int, str | None, int, str]:
    """Select CUDA explicitly when available, retaining a predictable CPU fallback."""

    if torch.cuda.is_available():
        sizes = {"speed": 416, "balanced": 640, "precision": 960}
        name = torch.cuda.get_device_name(0)
        return 0, "fp16", sizes[profile], f"CUDA · {name}"
    sizes = {"speed": 320, "balanced": 416, "precision": 512}
    return "cpu", None, sizes[profile], "CPU"


def _model_path() -> Path:
    configured = Path(os.getenv("CAMPUS_SENTINEL_MODEL", "models/yolo26n-pose.pt"))
    if configured.is_absolute():
        return configured
    repository_candidate = REPOSITORY_ROOT / configured
    if repository_candidate.is_file() or configured.parent != Path("."):
        return repository_candidate
    return REPOSITORY_ROOT / "models" / configured


def _decode_frame(data: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("frame JPEG inválido")
    return image


def _warm_up_model(
    model: YOLO,
    *,
    inference_size: int,
    device: str | int,
    quantization: str | None,
) -> None:
    """Pay one-time predictor initialization cost before a recorded video starts."""

    image = np.zeros((inference_size, inference_size, 3), dtype=np.uint8)
    options: dict[str, Any] = {
        "classes": [0],
        "imgsz": inference_size,
        "device": device,
        "verbose": False,
    }
    if quantization is not None:
        options["quantize"] = quantization
    model.predict(image, **options)


async def _send(websocket: WebSocket, lock: asyncio.Lock, event: dict[str, Any]) -> None:
    async with lock:
        await websocket.send_json(event)


async def _evaluate_and_send(
    coordinator: DecisionCoordinator,
    world_state: WorldState,
    websocket: WebSocket,
    lock: asyncio.Lock,
) -> None:
    """Deliver a Jev result as soon as it is ready, independently of later frames."""

    try:
        event = await coordinator.evaluate(world_state)
    # Keep provider and transport failures distinct from a normal/unknown decision.
    except Exception as error:  # noqa: BLE001
        event = {"type": "decision_error", "message": str(error)}
    await _send(websocket, lock, event)


def create_app() -> FastAPI:
    load_dotenv(REPOSITORY_ROOT / ".env")
    application = FastAPI(title="Campus Sentinel", docs_url=None, redoc_url=None)

    @application.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_ROOT / "index.html")

    @application.websocket("/ws/analyze")
    async def analyze(websocket: WebSocket) -> None:
        await websocket.accept()
        send_lock = asyncio.Lock()
        pending_decision: asyncio.Task[None] | None = None
        sdk_client: AsyncTypeSafeClient | None = None
        try:
            start = json.loads(await websocket.receive_text())
            if start.get("type") != "start" or start.get("source") not in {"camera", "video"}:
                await _send(websocket, send_lock, {"type": "fatal", "message": "fonte inválida"})
                return
            profile = start.get("profile", "balanced")
            if profile not in {"speed", "balanced", "precision"}:
                await _send(
                    websocket,
                    send_lock,
                    {"type": "fatal", "message": "perfil de desempenho inválido"},
                )
                return
            device, quantization, inference_size, compute_label = _compute_config(profile)

            model_path = _model_path()
            if not model_path.is_file():
                await _send(
                    websocket,
                    send_lock,
                    {"type": "fatal", "message": f"modelo não encontrado: {model_path}"},
                )
                return
            await _send(
                websocket,
                send_lock,
                {"type": "status", "stage": "loading", "message": "Carregando YOLO…"},
            )
            model = await asyncio.to_thread(YOLO, str(model_path))
            await asyncio.to_thread(
                _warm_up_model,
                model,
                inference_size=inference_size,
                device=device,
                quantization=quantization,
            )
            runtime = VisionRuntime(
                model,
                source_id=f"browser-{start['source']}",
                inference_size=inference_size,
                device=device,
                quantization=quantization,
            )

            coordinator: DecisionCoordinator | None = None
            if os.getenv("TYPESAFE_API_KEY", "").strip():
                sdk_client = AsyncTypeSafeClient()
                interval_ms = max(250, int(float(os.getenv("JEV_INTERVAL_SECONDS", "0.75")) * 1_000))
                coordinator = DecisionCoordinator(
                    JevDecisionEngine(sdk_client), interval_ms=interval_ms
                )
                jev_message = f"Jev ativo; avaliação a cada {interval_ms / 1_000:g}s"
            else:
                jev_message = "Jev desativado: TYPESAFE_API_KEY ausente"

            yolo_enabled = bool(start.get("yolo_enabled", True))
            jev_available = coordinator is not None
            jev_enabled = bool(start.get("jev_enabled", True)) and jev_available

            await _send(
                websocket,
                send_lock,
                {
                    "type": "status",
                    "stage": "ready",
                    "message": f"YOLO + ByteTrack em {compute_label}. {jev_message}",
                    "yolo_enabled": yolo_enabled,
                    "jev_enabled": jev_enabled,
                    "jev_available": jev_available,
                    "inference_size": inference_size,
                    "compute": compute_label,
                },
            )
            next_timestamp_ms: int | None = None
            next_request_id: int | None = None
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                if message.get("text") is not None:
                    control = json.loads(message["text"])
                    if control.get("type") == "stop":
                        break
                    if control.get("type") == "frame_meta":
                        next_timestamp_ms = max(0, int(control.get("timestamp_ms", 0)))
                        next_request_id = control.get("request_id")
                    if control.get("type") == "set_analysis":
                        yolo_enabled = bool(control.get("yolo_enabled", yolo_enabled))
                        requested_jev = bool(control.get("jev_enabled", jev_enabled))
                        jev_enabled = requested_jev and jev_available
                        next_timestamp_ms = None
                        next_request_id = None
                        if not jev_enabled and pending_decision is not None and not pending_decision.done():
                            pending_decision.cancel()
                            pending_decision = None
                        await _send(
                            websocket,
                            send_lock,
                            {
                                "type": "analysis_state",
                                "yolo_enabled": yolo_enabled,
                                "jev_enabled": jev_enabled,
                                "jev_available": jev_available,
                                "message": (
                                    "YOLO ativo; Jev ativo"
                                    if yolo_enabled and jev_enabled
                                    else "YOLO ativo; Jev desativado"
                                    if yolo_enabled
                                    else "YOLO desativado; captura pausada"
                                ),
                            },
                        )
                    continue
                data = message.get("bytes")
                if data is None or next_timestamp_ms is None or not yolo_enabled:
                    continue

                if pending_decision is not None and pending_decision.done():
                    await pending_decision
                    pending_decision = None

                try:
                    image = _decode_frame(data)
                    output = await asyncio.to_thread(runtime.process, image, next_timestamp_ms)
                    await _send(
                        websocket,
                        send_lock,
                        {
                            "type": "frame",
                            "frame_index": output.frame_index,
                            "request_id": next_request_id,
                            "people_count": output.people_count,
                            "inference_ms": round(output.inference_ms, 1),
                            "overlay": _overlay_json(output.perception_frame),
                            "world_state": (
                                None
                                if output.world_state is None
                                else _world_state_json(output.world_state)
                            ),
                        },
                    )
                    if (
                        jev_enabled
                        and coordinator is not None
                        and output.world_state is not None
                        and pending_decision is None
                        and coordinator.is_due(output.world_state)
                    ):
                        await _send(
                            websocket,
                            send_lock,
                            {
                                "type": "decision_started",
                                "observed_at_ms": output.world_state.observed_at_ms,
                            },
                        )
                        pending_decision = asyncio.create_task(
                            _evaluate_and_send(
                                coordinator,
                                output.world_state,
                                websocket,
                                send_lock,
                            )
                        )
                # This is the fault boundary for third-party model and image codecs.
                except Exception as error:  # noqa: BLE001
                    await _send(
                        websocket,
                        send_lock,
                        {"type": "frame_error", "message": str(error)},
                    )
                finally:
                    next_timestamp_ms = None
                    next_request_id = None
        except WebSocketDisconnect:
            pass
        # Keep an unexpected session failure isolated from the ASGI server.
        except Exception as error:  # noqa: BLE001
            try:
                await _send(websocket, send_lock, {"type": "fatal", "message": str(error)})
            except Exception:
                LOGGER.debug("WebSocket closed before fatal event could be sent", exc_info=True)
        finally:
            if pending_decision is not None and not pending_decision.done():
                pending_decision.cancel()
            if pending_decision is not None:
                with suppress(asyncio.CancelledError, Exception):
                    await pending_decision
            if sdk_client is not None:
                await sdk_client.aclose()

    return application


def _world_state_json(state: WorldState) -> dict[str, Any]:
    return asdict(state)


def _overlay_json(frame: PerceptionFrame) -> dict[str, Any]:
    return {
        "width": frame.image_width,
        "height": frame.image_height,
        "persons": [
            {
                "track_id": person.track_id,
                "confidence": round(person.confidence, 3),
                "bbox": {
                    "x_min": round(person.bounding_box.x_min, 1),
                    "y_min": round(person.bounding_box.y_min, 1),
                    "x_max": round(person.bounding_box.x_max, 1),
                    "y_max": round(person.bounding_box.y_max, 1),
                },
                "keypoints": [
                    {
                        "name": point.name,
                        "x": round(point.x, 1),
                        "y": round(point.y, 1),
                        "confidence": (
                            None if point.confidence is None else round(point.confidence, 3)
                        ),
                    }
                    for point in person.pose.points
                ],
            }
            for person in frame.persons
        ],
    }


app = create_app()
