"""Deterministic temporal and geometric evidence presented to the decision layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PersonFeatures:
    """Motion evidence for one track; missing values mean insufficient evidence."""

    track_id: int
    body_speed: float | None = None
    wrist_speed: float | None = None
    wrist_acceleration: float | None = None
    motion_intensity: float | None = None
    person_fallen: bool | None = None


@dataclass(frozen=True, slots=True)
class InteractionFeatures:
    """Pairwise evidence, normalized by body/box scale where applicable."""

    first_track_id: int
    second_track_id: int
    distance_between_people: float | None = None
    rapid_approach: bool | None = None
    wrist_to_head_distance: float | None = None
    wrist_to_torso_distance: float | None = None
    bbox_overlap: float | None = None
    possible_contact: bool | None = None
    interaction_duration_ms: int | None = None
    repeated_aggressive_motion: bool | None = None


@dataclass(frozen=True, slots=True)
class WorldState:
    """Clean evidence aggregated over one temporal window for Jev."""

    source_id: str
    observed_at_ms: int
    window_start_ms: int
    window_end_ms: int
    people: tuple[PersonFeatures, ...]
    interactions: tuple[InteractionFeatures, ...]
