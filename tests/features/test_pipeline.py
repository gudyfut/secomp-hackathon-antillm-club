import json
from dataclasses import asdict
from math import isfinite

import pytest

from contracts import BoundingBox, PerceptionFrame, PoseKeypoint, PoseKeypoints, TrackedPerson
from features import FeatureConfig, TemporalFeaturePipeline


def _person(
    track_id: int,
    x: float,
    *,
    height: float = 100.0,
    wrist_offset: float = 0.0,
    wrist_x_offset: float = 0.0,
    left_wrist_x_offset: float | None = None,
    right_wrist_x_offset: float | None = None,
    pose_scale: float = 1.0,
    visible_names: frozenset[str] | None = None,
    confidence: float = 0.9,
    pose: bool = True,
) -> TrackedPerson:
    points = ()
    if pose:
        points = tuple(
            PoseKeypoint(
                name,
                x
                + offset_x * pose_scale
                + (
                    left_wrist_x_offset
                    if name == "left_wrist" and left_wrist_x_offset is not None
                    else right_wrist_x_offset
                    if name == "right_wrist" and right_wrist_x_offset is not None
                    else wrist_x_offset
                    if "wrist" in name
                    else 0.0
                ),
                offset_y * pose_scale + wrist_offset if "wrist" in name else offset_y * pose_scale,
                confidence,
            )
            for name, offset_x, offset_y in (
                ("nose", 50.0, 10.0),
                ("left_shoulder", 35.0, 30.0),
                ("right_shoulder", 65.0, 30.0),
                ("left_elbow", 25.0, 50.0),
                ("right_elbow", 75.0, 50.0),
                ("left_wrist", 20.0, 70.0),
                ("right_wrist", 80.0, 70.0),
                ("left_hip", 40.0, 70.0),
                ("right_hip", 60.0, 70.0),
                ("left_knee", 40.0, 95.0),
                ("right_knee", 60.0, 95.0),
                ("left_ankle", 40.0, 120.0),
                ("right_ankle", 60.0, 120.0),
            )
            if visible_names is None or name in visible_names
        )
    return TrackedPerson(
        track_id=track_id,
        bounding_box=BoundingBox(x, 0.0, x + 100.0, height),
        pose=PoseKeypoints(points),
        confidence=confidence,
    )


def _frame(timestamp_ms: int, *people: TrackedPerson) -> PerceptionFrame:
    return PerceptionFrame("camera", timestamp_ms // 100, timestamp_ms, 1_000, 800, tuple(people))


def _pipeline(**changes: float) -> TemporalFeaturePipeline:
    config = FeatureConfig(
        world_state_interval_seconds=0.0,
        minimum_track_age_seconds=0.0,
        minimum_interaction_track_age_seconds=0.0,
        minimum_pair_observation_seconds=0.0,
        **changes,
    )
    return TemporalFeaturePipeline(config)


def test_first_sample_is_missing_and_stationary_sample_is_observed_zero() -> None:
    pipeline = _pipeline()
    first = pipeline.update(_frame(0, _person(1, 0.0)))
    second = pipeline.update(_frame(500, _person(1, 0.0)))
    assert first is not None and first.people[0].body_speed is None
    assert second is not None
    assert second.people[0].body_speed == pytest.approx(0.0)
    assert second.people[0].wrist_speed == pytest.approx(0.0)


def test_linear_speed_is_scale_normalized_and_global_translation_is_not_arm_motion() -> None:
    large = _pipeline()
    small = _pipeline()
    large.update(_frame(0, _person(1, 0.0, height=200.0, pose_scale=2.0)))
    large_state = large.update(
        _frame(1_000, _person(1, 100.0, height=200.0, pose_scale=2.0))
    )
    small.update(_frame(0, _person(1, 0.0, height=100.0)))
    small_state = small.update(_frame(1_000, _person(1, 50.0, height=100.0)))
    assert large_state is not None and small_state is not None
    assert large_state.people[0].body_speed == pytest.approx(0.5)
    assert small_state.people[0].body_speed == pytest.approx(0.5)
    assert large_state.people[0].wrist_speed == pytest.approx(0.0)


def test_local_wrist_motion_and_low_confidence_or_missing_pose() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0)))
    moved = pipeline.update(_frame(500, _person(1, 0.0, wrist_offset=40.0)))
    assert moved is not None and moved.people[0].wrist_speed is not None
    assert moved.people[0].wrist_speed > 0.0

    absent = _pipeline()
    absent.update(_frame(0, _person(1, 0.0, pose=False)))
    state = absent.update(_frame(500, _person(1, 0.0, pose=False)))
    assert state is not None and state.people[0].wrist_speed is None

    low = _pipeline()
    low.update(_frame(0, _person(1, 0.0, confidence=0.1)))
    state = low.update(_frame(500, _person(1, 0.0, wrist_offset=40.0, confidence=0.1)))
    assert state is not None and state.people[0].wrist_speed is None


@pytest.mark.parametrize(
    ("first_x", "second_x", "expected_sign"),
    [(300.0, 200.0, -1), (300.0, 400.0, 1), (300.0, 300.0, 0)],
)
def test_pair_distance_changes_are_retained_in_bounded_history(
    first_x: float, second_x: float, expected_sign: int
) -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, first_x)))
    state = pipeline.update(_frame(500, _person(1, 0.0), _person(2, second_x)))
    assert state is not None
    pair = pipeline._pairs[(1, 2)]
    delta = pair.samples[-1].distance - pair.samples[-2].distance  # type: ignore[operator]
    assert delta * expected_sign >= 0.0
    assert state.interactions[0].distance_between_people == pytest.approx(second_x / 100.0)


def test_iou_interaction_duration_and_invalid_time_do_not_create_invalid_numbers() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 50.0)))
    state = pipeline.update(_frame(500, _person(1, 0.0), _person(2, 50.0)))
    assert state is not None
    assert state.interactions[0].bbox_overlap == pytest.approx(1 / 3)
    assert state.interactions[0].interaction_duration_ms == 500
    invalid_time_state = pipeline.update(_frame(400, _person(1, 0.0)))
    assert invalid_time_state is None
    assert all(
        value is None or isfinite(value)
        for value in asdict(state)["people"][0].values()
        if isinstance(value, float)
    )


def test_large_gap_resets_continuity_and_expiry_removes_track_and_pair() -> None:
    pipeline = _pipeline(track_ttl_seconds=0.2, interaction_ttl_seconds=0.2)
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 200.0)))
    gap = pipeline.update(_frame(1_500, _person(1, 100.0)))
    assert gap is not None and gap.people[0].body_speed is None
    assert 2 not in pipeline._tracks
    assert not pipeline._pairs


def test_cadence_determinism_and_json_safety() -> None:
    frames = [_frame(ms, _person(1, ms / 10.0)) for ms in (0, 100, 250, 500)]
    config = FeatureConfig(world_state_interval_seconds=0.25, minimum_track_age_seconds=0.0)
    def run() -> list[object]:
        pipeline = TemporalFeaturePipeline(config)
        return [pipeline.update(frame) for frame in frames]

    outputs = [run(), run()]
    assert outputs[0] == outputs[1]
    assert [state is not None for state in outputs[0]] == [True, False, True, True]
    for state in outputs[0]:
        if state is not None:
            assert json.dumps(asdict(state), allow_nan=False)
