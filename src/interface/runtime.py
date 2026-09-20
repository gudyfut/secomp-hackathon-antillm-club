"""Runtime orchestration shared by the web transport and focused tests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any, Protocol

import numpy as np

from contracts import PerceptionFrame, WorldState
from decision.jev import JevDecisionAssessment, JevDecisionEngine, build_jev_state
from features import TemporalFeaturePipeline
from perception.adapters import ultralytics_result_to_frame


class PoseModel(Protocol):
    """Minimal Ultralytics surface required by one dashboard session."""

    def track(self, image: np.ndarray, **kwargs: Any) -> list[Any]: ...


@dataclass(frozen=True, slots=True)
class ProcessedFrame:
    perception_frame: PerceptionFrame
    frame_index: int
    people_count: int
    inference_ms: float
    world_state: WorldState | None


class VisionRuntime:
    """Own tracking and temporal feature state for exactly one browser connection."""

    def __init__(
        self,
        model: PoseModel,
        *,
        source_id: str,
        pipeline: TemporalFeaturePipeline | None = None,
        inference_size: int = 416,
        device: str | int = "cpu",
        quantization: str | None = None,
    ) -> None:
        if inference_size < 320 or inference_size % 32 != 0:
            raise ValueError("inference_size must be at least 320 and divisible by 32")
        self._model = model
        self._source_id = source_id
        self._pipeline = pipeline or TemporalFeaturePipeline()
        self._inference_size = inference_size
        self._device = device
        self._quantization = quantization
        self._frame_index = 0

    def process(self, image: np.ndarray, timestamp_ms: int) -> ProcessedFrame:
        started = perf_counter()
        model_options: dict[str, Any] = {
            "persist": True,
            "tracker": "bytetrack.yaml",
            "classes": [0],
            "imgsz": self._inference_size,
            "device": self._device,
            "verbose": False,
        }
        if self._quantization is not None:
            model_options["quantize"] = self._quantization
        result = self._model.track(image, **model_options)[0]
        inference_ms = (perf_counter() - started) * 1_000
        frame = ultralytics_result_to_frame(
            result,
            source_id=self._source_id,
            frame_index=self._frame_index,
            timestamp_ms=timestamp_ms,
            image_width=image.shape[1],
            image_height=image.shape[0],
        )
        state = self._pipeline.update(frame)
        processed = ProcessedFrame(
            perception_frame=frame,
            frame_index=self._frame_index,
            people_count=len(frame.persons),
            inference_ms=inference_ms,
            world_state=state,
        )
        self._frame_index += 1
        return processed


class DecisionCoordinator:
    """Rate-limit Jev independently from the video and feature cadences."""

    def __init__(self, engine: JevDecisionEngine, *, interval_ms: int = 2_000) -> None:
        if interval_ms <= 0:
            raise ValueError("interval_ms must be positive")
        self._engine = engine
        self._interval_ms = interval_ms
        self._last_requested_at_ms: int | None = None

    def is_due(self, world_state: WorldState) -> bool:
        if len(world_state.people) < 2 or not world_state.interactions:
            return False
        last = self._last_requested_at_ms
        return last is None or world_state.observed_at_ms - last >= self._interval_ms

    async def evaluate(self, world_state: WorldState) -> dict[str, Any]:
        self._last_requested_at_ms = world_state.observed_at_ms
        jev_input = build_jev_state(world_state)
        assessment = await self._engine.evaluate(world_state)
        return decision_event(assessment, jev_input)


def decision_event(
    assessment: JevDecisionAssessment, jev_input: dict[str, Any]
) -> dict[str, Any]:
    """Return the browser-safe event and its visible alert classification."""

    decision = assessment.decision
    event_name = decision.event.value if decision is not None else None
    if event_name in {"FIGHT", "ASSAULT"}:
        alert_level = "danger"
        headline = "Possível violência detectada"
    elif event_name in {"SUSPICIOUS_INTERACTION", "UNKNOWN_ANOMALY"}:
        alert_level = "warning"
        headline = "Interação suspeita — monitorar"
    elif event_name == "NORMAL":
        alert_level = "safe"
        headline = "Nenhuma ocorrência detectada"
    else:
        alert_level = "unknown"
        headline = "Evidência insuficiente"
    return {
        "type": "decision",
        "alert_level": alert_level,
        "headline": headline,
        "jev_input": jev_input,
        "assessment": asdict(assessment),
    }
