from contracts import FeaturePipeline, PerceptionFrame, WorldState
from tests.fixtures.synthetic import make_perception_frame, make_world_state


class SyntheticFeaturePipeline:
    def update(self, frame: PerceptionFrame) -> WorldState | None:
        return make_world_state() if frame.persons else None


def test_feature_pipeline_can_be_developed_without_yolo() -> None:
    pipeline: FeaturePipeline = SyntheticFeaturePipeline()

    state = pipeline.update(make_perception_frame())

    assert state is not None
    assert state.source_id == "synthetic-camera"
