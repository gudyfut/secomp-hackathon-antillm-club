"""Validate and compact ``WorldState`` into the state consumed by Jev."""

from __future__ import annotations

import math
from typing import Any

from contracts import InteractionFeatures, PersonFeatures, WorldState

_PERSON_FIELDS = (
    "body_speed",
    "wrist_speed",
    "wrist_acceleration",
    "motion_intensity",
    "person_fallen",
)
_INTERACTION_FIELDS = (
    "distance_between_people",
    "rapid_approach",
    "wrist_to_head_distance",
    "wrist_to_torso_distance",
    "bbox_overlap",
    "possible_contact",
    "interaction_duration_ms",
    "repeated_aggressive_motion",
)


class WorldStatePayloadError(ValueError):
    """Raised before an invalid or ambiguous state can be sent to Jev."""


def _number(value: float | None, field: str, *, nonnegative: bool = True) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value):
        raise WorldStatePayloadError(f"{field} must be finite")
    if nonnegative and value < 0:
        raise WorldStatePayloadError(f"{field} must be nonnegative")
    return round(value, 4)


def _person_json(person: PersonFeatures) -> dict[str, Any]:
    return {
        "track_id": person.track_id,
        "body_speed_body_heights_per_second": _number(person.body_speed, "body_speed"),
        "arm_motion_speed_body_heights_per_second": _number(person.wrist_speed, "wrist_speed"),
        "arm_motion_acceleration_body_heights_per_second_squared": _number(
            person.wrist_acceleration, "wrist_acceleration", nonnegative=False
        ),
        "motion_intensity_body_heights_per_second": _number(
            person.motion_intensity, "motion_intensity"
        ),
        "person_fallen": person.person_fallen,
    }


def _interaction_json(interaction: InteractionFeatures) -> dict[str, Any]:
    duration = interaction.interaction_duration_ms
    if duration is not None and duration < 0:
        raise WorldStatePayloadError("interaction_duration_ms must be nonnegative")
    overlap = _number(interaction.bbox_overlap, "bbox_overlap")
    if overlap is not None and overlap > 1:
        raise WorldStatePayloadError("bbox_overlap must be between 0 and 1")
    if interaction.repeated_aggressive_motion is True:
        evidence_level = "REPEATED_STRIKES"
    elif interaction.possible_contact is True:
        evidence_level = "SINGLE_HEAD_STRIKE"
    elif interaction.rapid_approach is True:
        evidence_level = "APPROACH_ONLY"
    elif any(
        value is False
        for value in (
            interaction.rapid_approach,
            interaction.possible_contact,
            interaction.repeated_aggressive_motion,
        )
    ):
        evidence_level = "NONE_OR_NEGATIVE"
    else:
        evidence_level = "UNKNOWN"
    return {
        "first_track_id": interaction.first_track_id,
        "second_track_id": interaction.second_track_id,
        "distance_between_people_body_heights": _number(
            interaction.distance_between_people, "distance_between_people"
        ),
        "rapid_approach": interaction.rapid_approach,
        "minimum_cross_person_wrist_to_head_distance_body_heights": _number(
            interaction.wrist_to_head_distance, "wrist_to_head_distance"
        ),
        "minimum_cross_person_wrist_to_torso_distance_body_heights": _number(
            interaction.wrist_to_torso_distance, "wrist_to_torso_distance"
        ),
        "bounding_box_iou": overlap,
        "possible_contact": interaction.possible_contact,
        "interaction_duration_ms": duration,
        "repeated_aggressive_motion": interaction.repeated_aggressive_motion,
        "pairwise_evidence_level": evidence_level,
    }


def _validate_structure(world_state: WorldState) -> None:
    if world_state.window_end_ms < world_state.window_start_ms:
        raise WorldStatePayloadError("window_end_ms must not precede window_start_ms")

    track_ids = [person.track_id for person in world_state.people]
    if len(track_ids) != len(set(track_ids)):
        raise WorldStatePayloadError("people must have unique track_id values")
    known_tracks = set(track_ids)

    pairs: set[tuple[int, int]] = set()
    for interaction in world_state.interactions:
        first = interaction.first_track_id
        second = interaction.second_track_id
        if first == second:
            raise WorldStatePayloadError("an interaction cannot reference the same track twice")
        if first not in known_tracks or second not in known_tracks:
            raise WorldStatePayloadError("interactions must reference tracks present in people")
        pair = tuple(sorted((first, second)))
        if pair in pairs:
            raise WorldStatePayloadError("each track pair may appear only once")
        pairs.add(pair)


def world_state_to_json(world_state: WorldState) -> dict[str, Any]:
    """Create a deterministic, compact payload with explicit units and null semantics."""

    _validate_structure(world_state)
    people = sorted(world_state.people, key=lambda person: person.track_id)
    interactions = sorted(
        world_state.interactions,
        key=lambda item: (item.first_track_id, item.second_track_id),
    )
    available_person = sum(
        getattr(person, field) is not None for person in people for field in _PERSON_FIELDS
    )
    available_interaction = sum(
        getattr(interaction, field) is not None
        for interaction in interactions
        for field in _INTERACTION_FIELDS
    )
    possible = len(people) * len(_PERSON_FIELDS) + len(interactions) * len(_INTERACTION_FIELDS)
    available = available_person + available_interaction

    return {
        "schema_version": "world-state.jev.v1",
        "observation_window": {
            "duration_ms": world_state.window_end_ms - world_state.window_start_ms,
        },
        "summary": {
            "people_count": len(people),
            "interaction_count": len(interactions),
            "available_signal_count": available,
            "possible_signal_count": possible,
            "signal_coverage": round(available / possible, 4) if possible else 0.0,
        },
        "semantics": {
            "null": "unknown_or_not_computable; never assume zero or false",
            "temporal_aggregation": (
                "motion values are recent peaks; interaction distances are recent minima except "
                "distance_between_people, which is current; separate peak/minimum fields are not "
                "necessarily simultaneous and must not be combined into an inferred strike"
            ),
            "distances": "normalized by skeleton-derived body scale; smaller means closer",
            "cross_person_wrist_distances": (
                "minimum of first-to-second and second-to-first directions"
            ),
            "speeds": "normalized body heights per second",
            "acceleration": "normalized body heights per second squared; may be negative",
            "bounding_box_iou": "0 means no overlap; 1 means complete overlap",
            "possible_contact": (
                "true only for a directionally correlated fast wrist approach reaching the head, "
                "or repeated high-energy entries toward the torso; one smooth torso reach is "
                "ambiguous and proximity alone is false"
            ),
            "unpaired_arm_motion": (
                "person-level arm speed or acceleration can be exercise, gesturing, or movement "
                "away from others; regardless of magnitude it is not aggression without "
                "pairwise possible_contact, repeated_aggressive_motion, or rapid_approach"
            ),
            "pair_admission": (
                "interactions are emitted only after both tracks stabilize and comparable torso, "
                "shoulder, hip, or limb segments indicate a similar apparent scene depth; cropped "
                "bounding-box height is never used for this decision"
            ),
            "hug_pattern": (
                "one smooth simultaneous two-sided reach toward the torsos is not marked as "
                "possible_contact; without head contact, repetition, fall, or instability it is "
                "compatible with a hug"
            ),
            "rapid_approach": (
                "closing body distance is contextual evidence only; by itself it may be a hug, "
                "greeting, passing movement, or camera projection"
            ),
            "pairwise_evidence_level": (
                "deterministic summary: NONE_OR_NEGATIVE and APPROACH_ONLY do not establish "
                "violence; SINGLE_HEAD_STRIKE is one high-speed directionally correlated head "
                "strike and can establish a one-sided assault without repetition; "
                "REPEATED_STRIKES is the strongest pairwise motion evidence"
            ),
            "person_fallen": (
                "current 2D pose appears horizontal; it does not prove another person caused "
                "the fall and requires temporal interaction evidence for a violence inference"
            ),
            "negative_evidence": (
                "small distance, bounding-box overlap, long proximity, or low/static motion "
                "alone are ordinary non-violent observations"
            ),
            "booleans": "deterministic evidence flags, not final incident judgments",
        },
        "people": [_person_json(person) for person in people],
        "interactions": [_interaction_json(interaction) for interaction in interactions],
    }


def build_jev_state(world_state: WorldState) -> dict[str, Any]:
    """Build the named state envelope referenced by all MVP questions."""

    return {"world_state": world_state_to_json(world_state)}
