from contracts import EventType, PerceptionFrame, WorldState
from tests.fixtures.synthetic import make_perception_frame, make_world_state


def test_synthetic_perception_frame_uses_project_contract() -> None:
    frame = make_perception_frame()

    assert isinstance(frame, PerceptionFrame)
    assert frame.persons[0].track_id == 1
    assert frame.image_width == 640


def test_synthetic_world_state_is_independent_from_yolo() -> None:
    state = make_world_state()

    assert isinstance(state, WorldState)
    assert state.interactions[0].possible_contact is True
    assert EventType.FIGHT.value == "FIGHT"
