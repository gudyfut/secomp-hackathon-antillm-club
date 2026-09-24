import pytest

from features import FeatureConfig, TemporalFeaturePipeline

from .test_pipeline import _frame, _person, _pipeline


def test_normal_walk_has_parallel_motion_and_stable_distance_history() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 300.0)))
    state = pipeline.update(_frame(500, _person(1, 50.0), _person(2, 350.0)))
    assert state is not None
    assert all(person.body_speed and person.body_speed > 0.0 for person in state.people)
    pair = pipeline._pairs[(1, 2)]
    assert pair.samples[-1].distance == pair.samples[-2].distance


def test_close_overlapping_people_without_motion_are_not_contact_evidence() -> None:
    pipeline = _pipeline()
    for timestamp_ms in (0, 200, 400, 600):
        state = pipeline.update(_frame(timestamp_ms, _person(1, 0.0), _person(2, 50.0)))

    assert state is not None
    interaction = state.interactions[0]
    assert interaction.distance_between_people == 0.5
    assert interaction.bbox_overlap == 1 / 3
    assert interaction.rapid_approach is False
    assert interaction.possible_contact is False
    assert interaction.repeated_aggressive_motion is False


def test_accelerating_toward_and_close_local_motion_remain_numeric_evidence() -> None:
    toward = _pipeline()
    toward.update(_frame(0, _person(1, 0.0), _person(2, 500.0)))
    toward.update(_frame(500, _person(1, 100.0), _person(2, 450.0)))
    state = toward.update(_frame(1_000, _person(1, 300.0), _person(2, 350.0)))
    assert state is not None
    pair = toward._pairs[(1, 2)]
    assert pair.samples[-1].distance < pair.samples[-2].distance
    assert state.interactions[0].rapid_approach is True

    close = TemporalFeaturePipeline()
    close.update(_frame(0, _person(1, 0.0), _person(2, 120.0)))
    state = close.update(
        _frame(500, _person(1, 0.0, wrist_offset=35.0), _person(2, 120.0, wrist_offset=-35.0))
    )
    assert state is not None
    assert all(person.wrist_speed is None or person.wrist_speed > 0.0 for person in state.people)


def test_one_sided_slap_preserves_contact_and_motion_peak() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 120.0)))
    state = pipeline.update(
        _frame(
            200,
            _person(1, 0.0, wrist_x_offset=90.0, wrist_offset=-60.0),
            _person(2, 120.0),
        )
    )

    assert state is not None
    assert state.people[0].wrist_speed is not None and state.people[0].wrist_speed > 2.0
    assert state.interactions[0].wrist_to_head_distance == 0.0
    assert state.interactions[0].possible_contact is True


def test_slow_single_head_reach_does_not_cross_strike_speed_threshold() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 120.0)))
    state = pipeline.update(
        _frame(
            800,
            _person(1, 0.0, wrist_x_offset=90.0, wrist_offset=-60.0),
            _person(2, 120.0),
        )
    )

    assert state is not None
    assert state.interactions[0].wrist_to_head_distance == 0.0
    assert state.interactions[0].possible_contact is False


def test_contact_is_symmetric_when_the_higher_track_id_moves() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 120.0)))
    state = pipeline.update(
        _frame(
            200,
            _person(1, 0.0),
            _person(2, 120.0, wrist_x_offset=-90.0, wrist_offset=-60.0),
        )
    )

    assert state is not None
    assert state.interactions[0].wrist_to_head_distance == 0.0
    assert state.interactions[0].possible_contact is True


def test_fast_arm_moving_away_is_not_combined_with_other_persons_nearby_wrist() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 50.0)))
    state = pipeline.update(
        _frame(
            200,
            _person(1, 0.0, wrist_x_offset=-80.0),
            _person(2, 50.0),
        )
    )

    assert state is not None
    assert state.people[0].wrist_speed is not None and state.people[0].wrist_speed > 1.9
    assert state.interactions[0].distance_between_people == pytest.approx(0.5)
    assert state.interactions[0].possible_contact is False
    assert state.interactions[0].repeated_aggressive_motion is None


def test_moving_wrist_is_not_combined_with_same_persons_stationary_nearby_wrist() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 50.0)))
    state = pipeline.update(
        _frame(
            200,
            _person(1, 0.0, left_wrist_x_offset=-80.0),
            _person(2, 50.0),
        )
    )

    assert state is not None
    assert state.people[0].wrist_speed is not None
    assert state.people[0].wrist_speed >= 1.0
    assert state.interactions[0].wrist_to_torso_distance <= 0.1
    assert state.interactions[0].possible_contact is False


def test_fast_arm_motion_far_from_the_other_person_is_not_contact() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 250.0)))
    state = pipeline.update(
        _frame(200, _person(1, 0.0, wrist_offset=-80.0), _person(2, 250.0))
    )

    assert state is not None
    assert state.people[0].wrist_speed is not None and state.people[0].wrist_speed > 1.9
    assert state.interactions[0].possible_contact is False


def test_single_reciprocal_torso_reach_is_compatible_with_a_hug() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 300.0)))
    state = pipeline.update(
        _frame(
            200,
            _person(1, 0.0, wrist_x_offset=80.0),
            _person(2, 120.0, wrist_x_offset=-80.0),
        )
    )

    assert state is not None
    assert state.interactions[0].wrist_to_torso_distance == 0.0
    assert state.interactions[0].rapid_approach is True
    assert state.interactions[0].possible_contact is False
    assert state.interactions[0].repeated_aggressive_motion is None


def test_repeated_forceful_torso_entries_remain_contact_evidence() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 120.0)))
    pipeline.update(
        _frame(200, _person(1, 0.0, wrist_x_offset=80.0), _person(2, 120.0))
    )
    pipeline.update(_frame(400, _person(1, 0.0), _person(2, 120.0)))
    pipeline.update(_frame(600, _person(1, 0.0), _person(2, 120.0)))
    state = pipeline.update(
        _frame(800, _person(1, 0.0, wrist_x_offset=80.0), _person(2, 120.0))
    )

    assert state is not None
    assert state.interactions[0].possible_contact is True
    assert state.interactions[0].repeated_aggressive_motion is True


def test_different_apparent_body_scales_do_not_form_an_interaction() -> None:
    pipeline = _pipeline()
    pipeline.update(
        _frame(
            0,
            _person(1, 0.0, height=200.0, pose_scale=2.0),
            _person(2, 100.0, height=100.0),
        )
    )
    state = pipeline.update(
        _frame(
            200,
            _person(1, 0.0, height=200.0, pose_scale=2.0, wrist_x_offset=80.0),
            _person(2, 100.0, height=100.0),
        )
    )

    assert state is not None
    assert state.interactions == ()


def test_partial_upper_body_uses_common_shoulder_scale_instead_of_box_height() -> None:
    upper_body = frozenset(
        {
            "nose",
            "left_shoulder",
            "right_shoulder",
            "left_elbow",
            "right_elbow",
            "left_wrist",
            "right_wrist",
        }
    )
    pipeline = _pipeline()
    pipeline.update(
        _frame(
            0,
            _person(1, 0.0, height=75.0, visible_names=upper_body),
            _person(2, 120.0),
        )
    )
    state = pipeline.update(
        _frame(
            200,
            _person(
                1,
                0.0,
                height=75.0,
                visible_names=upper_body,
                wrist_x_offset=90.0,
                wrist_offset=-60.0,
            ),
            _person(2, 120.0),
        )
    )

    assert state is not None
    assert len(state.interactions) == 1
    assert state.interactions[0].possible_contact is True


def test_cropped_box_height_does_not_change_skeleton_normalized_contact() -> None:
    full = _pipeline()
    cropped = _pipeline()
    full.update(_frame(0, _person(1, 0.0, height=120.0), _person(2, 120.0)))
    cropped.update(_frame(0, _person(1, 0.0, height=65.0), _person(2, 120.0)))
    full_state = full.update(
        _frame(
            200,
            _person(1, 0.0, height=120.0, wrist_x_offset=90.0, wrist_offset=-60.0),
            _person(2, 120.0),
        )
    )
    cropped_state = cropped.update(
        _frame(
            200,
            _person(1, 0.0, height=65.0, wrist_x_offset=90.0, wrist_offset=-60.0),
            _person(2, 120.0),
        )
    )

    assert full_state is not None and cropped_state is not None
    assert full_state.interactions[0].possible_contact is True
    assert cropped_state.interactions[0].possible_contact is True
    assert cropped_state.people[0].wrist_speed == pytest.approx(
        full_state.people[0].wrist_speed
    )


def test_bbox_crop_change_does_not_create_false_body_approach() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0, height=120.0), _person(2, 120.0)))
    state = pipeline.update(
        _frame(200, _person(1, 0.0, height=65.0), _person(2, 120.0))
    )

    assert state is not None
    assert state.people[0].body_speed == pytest.approx(0.0)
    assert state.interactions[0].rapid_approach is False


def test_new_tracks_wait_for_age_and_pair_baseline_before_interaction() -> None:
    pipeline = TemporalFeaturePipeline(
        FeatureConfig(world_state_interval_seconds=0.0, minimum_track_age_seconds=0.0)
    )
    for timestamp_ms in (0, 300, 500):
        state = pipeline.update(
            _frame(timestamp_ms, _person(1, 0.0), _person(2, 120.0))
        )
        assert state is not None and state.interactions == ()

    stable = pipeline.update(_frame(700, _person(1, 0.0), _person(2, 120.0)))
    assert stable is not None
    assert len(stable.interactions) == 1


def test_repeated_contact_motion_is_retained_across_recent_window() -> None:
    pipeline = _pipeline()
    pipeline.update(_frame(0, _person(1, 0.0), _person(2, 120.0)))
    pipeline.update(
        _frame(
            200,
            _person(1, 0.0, wrist_x_offset=90.0, wrist_offset=-60.0),
            _person(2, 120.0),
        )
    )
    pipeline.update(_frame(400, _person(1, 0.0), _person(2, 120.0)))
    pipeline.update(_frame(600, _person(1, 0.0), _person(2, 120.0)))
    state = pipeline.update(
        _frame(
            800,
            _person(1, 0.0, wrist_x_offset=90.0, wrist_offset=-60.0),
            _person(2, 120.0),
        )
    )

    assert state is not None
    assert state.interactions[0].possible_contact is True
    assert state.interactions[0].repeated_aggressive_motion is True
