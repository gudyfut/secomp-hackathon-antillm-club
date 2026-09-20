from features import TemporalFeaturePipeline

from .test_pipeline import _frame, _person, _pipeline


def test_normal_walk_has_parallel_motion_and_stable_distance_history() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 300.0)))
    state = pipeline.update(_frame(500, _person(1, 50.0), _person(2, 350.0)))
    assert state is not None
    assert all(person.body_speed and person.body_speed > 0.0 for person in state.people)
    pair = pipeline._pairs[(1, 2)]
    assert pair.samples[-1].distance == pair.samples[-2].distance


def test_accelerating_toward_and_close_local_motion_remain_numeric_evidence() -> None:
    toward = _pipeline()
    toward.update(_frame(0, _person(1, 0.0), _person(2, 500.0)))
    toward.update(_frame(500, _person(1, 100.0), _person(2, 450.0)))
    state = toward.update(_frame(1_000, _person(1, 300.0), _person(2, 350.0)))
    assert state is not None
    pair = toward._pairs[(1, 2)]
    assert pair.samples[-1].distance < pair.samples[-2].distance

    close = TemporalFeaturePipeline()
    close.update(_frame(0, _person(1, 0.0), _person(2, 120.0)))
    state = close.update(
        _frame(500, _person(1, 0.0, wrist_offset=35.0), _person(2, 120.0, wrist_offset=-35.0))
    )
    assert state is not None
    assert all(person.wrist_speed is None or person.wrist_speed > 0.0 for person in state.people)
