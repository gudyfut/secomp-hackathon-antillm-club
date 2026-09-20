from contracts import PerceptionFrame
from tests.fixtures.synthetic import make_perception_frame


def test_perception_output_can_be_constructed_without_external_sdk_types() -> None:
    frame = make_perception_frame()

    assert isinstance(frame, PerceptionFrame)
    assert len(frame.persons) == 2
