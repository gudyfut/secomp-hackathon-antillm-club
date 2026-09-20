"""Objective observations produced by the perception boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Axis-aligned bounding box in source-image pixel coordinates."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass(frozen=True, slots=True)
class PoseKeypoint:
    """Named pose point in source-image pixels with detector confidence."""

    name: str
    x: float
    y: float
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class PoseKeypoints:
    """Pose points belonging to one tracked person."""

    points: tuple[PoseKeypoint, ...]


@dataclass(frozen=True, slots=True)
class TrackedPerson:
    """One person observed in a frame after tracking association."""

    track_id: int
    bounding_box: BoundingBox
    pose: PoseKeypoints
    confidence: float


@dataclass(frozen=True, slots=True)
class PerceptionFrame:
    """SDK-independent perception output for exactly one source frame."""

    source_id: str
    frame_index: int
    timestamp_ms: int
    image_width: int
    image_height: int
    persons: tuple[TrackedPerson, ...]
