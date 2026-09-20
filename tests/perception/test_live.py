from contracts import InteractionFeatures, PersonFeatures, WorldState
from perception.live import format_world_state


def test_live_formatter_includes_all_contract_features() -> None:
    state = WorldState(
        source_id="0",
        observed_at_ms=500,
        window_start_ms=0,
        window_end_ms=500,
        people=(PersonFeatures(track_id=1, body_speed=0.5, wrist_speed=0.0),),
        interactions=(InteractionFeatures(first_track_id=1, second_track_id=2, bbox_overlap=0.25),),
    )

    output = format_world_state(state)

    assert "WORLD STATE" in output
    assert "body_speed=0.5" in output
    assert "person_fallen=None" in output
    assert "bbox_overlap=0.25" in output
    assert "repeated_aggressive_motion=None" in output
