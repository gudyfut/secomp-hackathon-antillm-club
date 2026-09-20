"""Live camera runner that bridges perception observations to a feature pipeline."""

from __future__ import annotations

from dataclasses import fields
from time import perf_counter
from typing import TYPE_CHECKING

from contracts import WorldState

from .adapters import ultralytics_result_to_frame

if TYPE_CHECKING:
    from contracts import FeaturePipeline


def format_world_state(state: WorldState) -> str:
    """Format only contract evidence emitted by the feature pipeline for terminal output."""
    lines = [
        "WORLD STATE",
        f"timestamp: {state.observed_at_ms} ms",
        f"source: {state.source_id}",
        f"window: {state.window_start_ms}..{state.window_end_ms} ms",
        "persons:",
    ]
    for person in state.people:
        values = ", ".join(
            f"{field.name}={getattr(person, field.name)!r}" for field in fields(person)
        )
        lines.append(f"  {values}")
    lines.append("interactions:")
    for interaction in state.interactions:
        values = ", ".join(
            f"{field.name}={getattr(interaction, field.name)!r}" for field in fields(interaction)
        )
        lines.append(f"  {values}")
    return "\n".join(lines)


def run_live(source: str | int, pipeline: FeaturePipeline, model_path: str = "yolo26n-pose.pt") -> None:
    """Run YOLO26 pose tracking from source until `q` or Escape closes its preview window."""
    try:
        import cv2
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError(
            "Instale dependencias de perception: python -m pip install -e '.[perception]'"
        ) from error

    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Nao foi possivel abrir source {source!r}")

    model = YOLO(model_path)
    source_id = str(source)
    frame_index = 0
    started_at = perf_counter()
    fps_started_at = started_at
    fps_frames = 0
    fps = 0.0
    try:
        while True:
            ok, image = capture.read()
            if not ok:
                break
            result = model.track(
                image, persist=True, tracker="bytetrack.yaml", classes=[0], verbose=False
            )[0]
            now = perf_counter()
            timestamp_ms = int((now - started_at) * 1_000)
            frame = ultralytics_result_to_frame(
                result,
                source_id=source_id,
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                image_width=image.shape[1],
                image_height=image.shape[0],
            )
            state = pipeline.update(frame)
            if state is not None:
                print(format_world_state(state), flush=True)

            fps_frames += 1
            elapsed = now - fps_started_at
            if elapsed >= 1.0:
                fps = fps_frames / elapsed
                fps_started_at = now
                fps_frames = 0
            preview = result.plot()
            emitted = "yes" if state is not None else "no"
            cv2.putText(preview, f"FPS: {fps:.1f}", (12, 28), 0, 0.7, (0, 255, 0), 2)
            cv2.putText(preview, "Tracker: ByteTrack active", (12, 56), 0, 0.7, (0, 255, 0), 2)
            cv2.putText(preview, f"Persons: {len(frame.persons)}", (12, 84), 0, 0.7, (0, 255, 0), 2)
            cv2.putText(preview, f"WorldState emitted: {emitted}", (12, 112), 0, 0.7, (0, 255, 0), 2)
            cv2.imshow("Campus Sentinel - YOLO26 Pose", preview)
            if cv2.waitKey(1) & 0xFF in {27, ord("q")}:
                break
            frame_index += 1
    finally:
        capture.release()
        cv2.destroyAllWindows()
