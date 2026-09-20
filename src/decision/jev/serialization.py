"""Conversion from stable project contracts to the JSON state consumed by Jev."""

from __future__ import annotations

from typing import Any

from contracts import WorldState


def world_state_to_json(world_state: WorldState) -> dict[str, Any]:
    """Serialize a ``WorldState`` without leaking Python or SDK-specific objects."""

    return {
        "source_id": world_state.source_id,
        "observed_at_ms": world_state.observed_at_ms,
        "window_start_ms": world_state.window_start_ms,
        "window_end_ms": world_state.window_end_ms,
        "people": [
            {
                "track_id": person.track_id,
                "body_speed": person.body_speed,
                "wrist_speed": person.wrist_speed,
                "wrist_acceleration": person.wrist_acceleration,
                "motion_intensity": person.motion_intensity,
                "person_fallen": person.person_fallen,
            }
            for person in world_state.people
        ],
        "interactions": [
            {
                "first_track_id": interaction.first_track_id,
                "second_track_id": interaction.second_track_id,
                "distance_between_people": interaction.distance_between_people,
                "rapid_approach": interaction.rapid_approach,
                "wrist_to_head_distance": interaction.wrist_to_head_distance,
                "wrist_to_torso_distance": interaction.wrist_to_torso_distance,
                "bbox_overlap": interaction.bbox_overlap,
                "possible_contact": interaction.possible_contact,
                "interaction_duration_ms": interaction.interaction_duration_ms,
                "repeated_aggressive_motion": interaction.repeated_aggressive_motion,
            }
            for interaction in world_state.interactions
        ],
    }


def build_jev_state(world_state: WorldState) -> dict[str, Any]:
    """Build the named state envelope referenced by the provisional question."""

    return {"worldState": world_state_to_json(world_state)}
