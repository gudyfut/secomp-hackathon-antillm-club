from __future__ import annotations

import asyncio
from types import SimpleNamespace

import numpy as np
import pytest

from contracts import (
    Action,
    DecisionResult,
    EventType,
    InteractionFeatures,
    PersonFeatures,
    Severity,
    Urgency,
    WorldState,
)
from decision.jev import ChoiceJudgment, DecisionStatus, JevDecisionAssessment, JevUsage
from features import FeatureConfig, TemporalFeaturePipeline
from interface.app import (
    REPOSITORY_ROOT,
    _compute_config,
    _evaluate_and_send,
    _model_path,
    _warm_up_model,
)
from interface.runtime import DecisionCoordinator, VisionRuntime, decision_event


class _Tensor:
    def __init__(self, value: object) -> None:
        self._value = value

    def cpu(self) -> _Tensor:
        return self

    def tolist(self) -> object:
        return self._value


class _Result:
    def __init__(self, image: np.ndarray) -> None:
        self.boxes = SimpleNamespace(
            id=_Tensor([7]),
            xyxy=_Tensor([[10.0, 10.0, 90.0, 190.0]]),
            conf=_Tensor([0.95]),
        )
        points = [[50.0 + index, 30.0 + index, 0.9] for index in range(17)]
        self.keypoints = SimpleNamespace(data=_Tensor([points]))
        self._image = image

    def plot(self) -> np.ndarray:
        return self._image.copy()


class _Model:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def track(self, image: np.ndarray, **kwargs: object) -> list[_Result]:
        self.kwargs = kwargs
        return [_Result(image)]


def _state(*, people_count: int = 2, timestamp_ms: int = 1_000) -> WorldState:
    people = tuple(PersonFeatures(track_id=index + 1) for index in range(people_count))
    interactions = (
        (InteractionFeatures(first_track_id=1, second_track_id=2, bbox_overlap=0.2),)
        if people_count >= 2
        else ()
    )
    return WorldState("test", timestamp_ms, 0, timestamp_ms, people, interactions)


def _judgment(choice: str) -> ChoiceJudgment:
    return ChoiceJudgment(choice, 0.9, {choice: 0.9})


def _assessment(event: EventType | None) -> JevDecisionAssessment:
    decision = (
        None
        if event is None
        else DecisionResult(event, Severity.HIGH, Urgency.HIGH, Action.ALERT, 1_000)
    )
    return JevDecisionAssessment(
        status=(DecisionStatus.INSUFFICIENT_EVIDENCE if event is None else DecisionStatus.DECIDED),
        decision=decision,
        evidence_quality=_judgment("INSUFFICIENT" if event is None else "SUFFICIENT"),
        event=_judgment(event.value if event is not None else "NORMAL"),
        severity=_judgment("HIGH"),
        urgency=_judgment("HIGH"),
        action=_judgment("ALERT"),
        world_state_observed_at_ms=1_000,
        model="jev-test",
        usage=JevUsage(10, 2),
    )


def test_vision_runtime_connects_yolo_adapter_and_feature_pipeline() -> None:
    model = _Model()
    pipeline = TemporalFeaturePipeline(
        FeatureConfig(world_state_interval_seconds=0.0, minimum_track_age_seconds=0.0)
    )
    runtime = VisionRuntime(model, source_id="browser-camera", pipeline=pipeline)

    output = runtime.process(np.zeros((200, 100, 3), dtype=np.uint8), 250)

    assert output.frame_index == 0
    assert output.people_count == 1
    assert output.world_state is not None
    assert output.world_state.source_id == "browser-camera"
    assert model.kwargs == {
        "persist": True,
        "tracker": "bytetrack.yaml",
        "classes": [0],
        "imgsz": 416,
        "device": "cpu",
        "verbose": False,
    }


def test_vision_runtime_rejects_invalid_inference_size() -> None:
    with pytest.raises(ValueError, match="divisible by 32"):
        VisionRuntime(_Model(), source_id="test", inference_size=400)


def test_compute_config_prefers_cuda_and_fp16(monkeypatch) -> None:
    monkeypatch.setattr("interface.app.torch.cuda.is_available", lambda: True)
    monkeypatch.setattr("interface.app.torch.cuda.get_device_name", lambda index: "Test GPU")

    assert _compute_config("balanced") == (0, "fp16", 640, "CUDA · Test GPU")


def test_compute_config_retains_cpu_fallback(monkeypatch) -> None:
    monkeypatch.setattr("interface.app.torch.cuda.is_available", lambda: False)

    assert _compute_config("balanced") == ("cpu", None, 416, "CPU")


def test_model_warmup_uses_selected_compute_configuration() -> None:
    class Model:
        def __init__(self) -> None:
            self.image: np.ndarray | None = None
            self.kwargs: dict[str, object] = {}

        def predict(self, image: np.ndarray, **kwargs: object) -> None:
            self.image = image
            self.kwargs = kwargs

    model = Model()
    _warm_up_model(  # type: ignore[arg-type]
        model, inference_size=640, device=0, quantization="fp16"
    )

    assert model.image is not None
    assert model.image.shape == (640, 640, 3)
    assert model.kwargs == {
        "classes": [0],
        "imgsz": 640,
        "device": 0,
        "quantize": "fp16",
        "verbose": False,
    }


def test_model_basename_from_env_falls_back_to_models_directory(monkeypatch) -> None:
    monkeypatch.setenv("CAMPUS_SENTINEL_MODEL", "yolo26n-pose.pt")

    assert _model_path() == REPOSITORY_ROOT / "models" / "yolo26n-pose.pt"


def test_decision_coordinator_requires_interaction_and_rate_limits_calls() -> None:
    coordinator = DecisionCoordinator(SimpleNamespace(), interval_ms=2_000)  # type: ignore[arg-type]

    assert not coordinator.is_due(_state(people_count=1))
    assert coordinator.is_due(_state(timestamp_ms=1_000))
    coordinator._last_requested_at_ms = 1_000
    assert not coordinator.is_due(_state(timestamp_ms=2_999))
    assert coordinator.is_due(_state(timestamp_ms=3_000))


def test_decision_event_only_marks_fight_or_assault_as_violence() -> None:
    fight = decision_event(_assessment(EventType.FIGHT), {"world_state": {}})
    suspicious = decision_event(
        _assessment(EventType.SUSPICIOUS_INTERACTION), {"world_state": {}}
    )
    insufficient = decision_event(_assessment(None), {"world_state": {}})

    assert fight["alert_level"] == "danger"
    assert suspicious["alert_level"] == "warning"
    assert insufficient["alert_level"] == "unknown"
    assert insufficient["assessment"]["decision"] is None


def test_coordinator_exposes_exact_jev_input_and_mapped_output() -> None:
    assessment = _assessment(EventType.NORMAL)

    class Engine:
        async def evaluate(self, world_state: WorldState) -> JevDecisionAssessment:
            return assessment

    coordinator = DecisionCoordinator(Engine(), interval_ms=1_000)  # type: ignore[arg-type]
    event = asyncio.run(coordinator.evaluate(_state()))

    assert event["jev_input"]["world_state"]["schema_version"] == "world-state.jev.v1"
    assert event["assessment"]["decision"]["event"] is EventType.NORMAL


def test_background_decision_is_sent_without_waiting_for_another_frame() -> None:
    class Coordinator:
        async def evaluate(self, world_state: WorldState) -> dict[str, object]:
            return {"type": "decision", "observed_at_ms": world_state.observed_at_ms}

    class WebSocket:
        def __init__(self) -> None:
            self.events: list[dict[str, object]] = []

        async def send_json(self, event: dict[str, object]) -> None:
            self.events.append(event)

    socket = WebSocket()
    asyncio.run(
        _evaluate_and_send(  # type: ignore[arg-type]
            Coordinator(), _state(timestamp_ms=3_000), socket, asyncio.Lock()
        )
    )

    assert socket.events == [{"type": "decision", "observed_at_ms": 3_000}]


def test_background_decision_reports_jev_failure_separately() -> None:
    class Coordinator:
        async def evaluate(self, world_state: WorldState) -> dict[str, object]:
            raise RuntimeError("provider unavailable")

    class WebSocket:
        def __init__(self) -> None:
            self.events: list[dict[str, object]] = []

        async def send_json(self, event: dict[str, object]) -> None:
            self.events.append(event)

    socket = WebSocket()
    asyncio.run(
        _evaluate_and_send(  # type: ignore[arg-type]
            Coordinator(), _state(), socket, asyncio.Lock()
        )
    )

    assert socket.events == [{"type": "decision_error", "message": "provider unavailable"}]
