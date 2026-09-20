"""Synthetic input and readable logging shared by decision examples."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from contracts import InteractionFeatures, PersonFeatures, WorldState


def make_example_world_state() -> WorldState:
    """Return a complete synthetic interaction state for examples only."""

    return WorldState(
        source_id="synthetic-decision-example",
        observed_at_ms=1_000,
        window_start_ms=0,
        window_end_ms=1_000,
        people=(
            PersonFeatures(
                track_id=1,
                body_speed=1.2,
                wrist_speed=2.1,
                wrist_acceleration=1.4,
                motion_intensity=0.8,
                person_fallen=False,
            ),
            PersonFeatures(
                track_id=2,
                body_speed=0.8,
                wrist_speed=1.5,
                wrist_acceleration=0.7,
                motion_intensity=0.6,
                person_fallen=False,
            ),
        ),
        interactions=(
            InteractionFeatures(
                first_track_id=1,
                second_track_id=2,
                distance_between_people=0.45,
                rapid_approach=True,
                wrist_to_head_distance=0.3,
                wrist_to_torso_distance=0.25,
                bbox_overlap=0.2,
                possible_contact=True,
                interaction_duration_ms=800,
                repeated_aggressive_motion=None,
            ),
        ),
    )


def _json_default(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def print_json(label: str, value: Any) -> None:
    """Print one labeled JSON section for human inspection."""

    print(f"\n=== {label} ===")
    print(json.dumps(value, indent=2, ensure_ascii=False, default=_json_default))
