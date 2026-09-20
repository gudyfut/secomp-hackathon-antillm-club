"""Small, dependency-free fixtures for parallel module development."""

from contracts import (
    BoundingBox,
    InteractionFeatures,
    PerceptionFrame,
    PersonFeatures,
    PoseKeypoint,
    PoseKeypoints,
    TrackedPerson,
    WorldState,
)


def make_perception_frame() -> PerceptionFrame:
    """Return a two-person frame without requiring YOLO or image files."""

    pose = PoseKeypoints(
        points=(
            PoseKeypoint(name="nose", x=100.0, y=80.0, confidence=0.95),
            PoseKeypoint(name="left_wrist", x=90.0, y=150.0, confidence=0.88),
        )
    )
    return PerceptionFrame(
        source_id="synthetic-camera",
        frame_index=12,
        timestamp_ms=400,
        image_width=640,
        image_height=480,
        persons=(
            TrackedPerson(1, BoundingBox(60.0, 50.0, 160.0, 280.0), pose, 0.94),
            TrackedPerson(2, BoundingBox(170.0, 55.0, 270.0, 285.0), pose, 0.92),
        ),
    )


def make_world_state() -> WorldState:
    """Return synthetic interaction evidence without perception dependencies."""

    return WorldState(
        source_id="synthetic-camera",
        observed_at_ms=1_000,
        window_start_ms=0,
        window_end_ms=1_000,
        people=(
            PersonFeatures(track_id=1, body_speed=1.2, wrist_speed=2.1),
            PersonFeatures(track_id=2, body_speed=0.8, wrist_speed=1.5),
        ),
        interactions=(
            InteractionFeatures(
                first_track_id=1,
                second_track_id=2,
                distance_between_people=0.45,
                rapid_approach=True,
                bbox_overlap=0.2,
                possible_contact=True,
                interaction_duration_ms=800,
            ),
        ),
    )
