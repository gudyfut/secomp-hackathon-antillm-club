"""Project-owned types for the provisional Jev assessment boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class PrototypeAssessment(StrEnum):
    """Temporary assessment vocabulary used while MVP questions are calibrated."""

    NO_CLEAR_CONCERN = "no_clear_concern"
    CONCERNING_INTERACTION = "concerning_interaction"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class JevUsage:
    """Token telemetry reported by the API; missing values remain unknown."""

    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True, slots=True)
class JevAssessment:
    """SDK-independent result returned by the provisional Jev evaluator."""

    assessment: PrototypeAssessment
    confidence: float
    probabilities: Mapping[str, float]
    model: str
    usage: JevUsage


class JevResponseError(RuntimeError):
    """Raised when a successful API response violates the expected question contract."""
