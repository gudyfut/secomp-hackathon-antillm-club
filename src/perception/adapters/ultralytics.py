"""Convert Ultralytics pose-tracking results into project-owned observations."""

from __future__ import annotations

from typing import Any

from contracts import BoundingBox, PerceptionFrame, PoseKeypoint, PoseKeypoints, TrackedPerson

COCO_POSE_KEYPOINT_NAMES = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)


def _to_list(value: Any) -> list[Any]:
    """Copy tensor-like SDK data into ordinary Python lists."""
    if value is None:
        return []
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        value = value.tolist()
    return list(value)


def ultralytics_result_to_frame(
    result: Any,
    *,
    source_id: str,
    frame_index: int,
    timestamp_ms: int,
    image_width: int,
    image_height: int,
) -> PerceptionFrame:
    """Return tracked persons from one Ultralytics pose result as a `PerceptionFrame`."""
    boxes = getattr(result, "boxes", None)
    track_ids = _to_list(getattr(boxes, "id", None))
    if boxes is None or not track_ids:
        return PerceptionFrame(
            source_id, frame_index, timestamp_ms, image_width, image_height, ()
        )

    coordinates = _to_list(boxes.xyxy)
    confidences = _to_list(boxes.conf)
    keypoints = _to_list(getattr(getattr(result, "keypoints", None), "data", None))
    if not (len(track_ids) == len(coordinates) == len(confidences) == len(keypoints)):
        raise ValueError("Ultralytics boxes and keypoints must have matching tracked rows")

    persons = tuple(
        TrackedPerson(
            track_id=int(track_id),
            bounding_box=BoundingBox(*(float(value) for value in coordinates[index])),
            pose=PoseKeypoints(
                tuple(
                    PoseKeypoint(
                        name=name,
                        x=float(point[0]),
                        y=float(point[1]),
                        confidence=float(point[2]) if len(point) > 2 else None,
                    )
                    for name, point in zip(COCO_POSE_KEYPOINT_NAMES, keypoints[index], strict=True)
                )
            ),
            confidence=float(confidences[index]),
        )
        for index, track_id in enumerate(track_ids)
    )
    return PerceptionFrame(source_id, frame_index, timestamp_ms, image_width, image_height, persons)
