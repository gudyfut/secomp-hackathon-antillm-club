"""Project-owned types at the Jev SDK boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from contracts import DecisionResult


class DecisionStatus(StrEnum):
    DECIDED = "DECIDED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True, slots=True)
class ChoiceJudgment:
    """One Jev choice detached from the SDK response model."""

    choice: str
    confidence: float
    probabilities: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class JevUsage:
    """Token telemetry reported by the API; it is not billing information."""

    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True, slots=True)
class JevDecisionAssessment:
    """Full Jev assessment; ``decision`` is absent if evidence is insufficient."""

    status: DecisionStatus
    decision: DecisionResult | None
    evidence_quality: ChoiceJudgment
    event: ChoiceJudgment
    severity: ChoiceJudgment
    urgency: ChoiceJudgment
    action: ChoiceJudgment
    world_state_observed_at_ms: int
    model: str
    usage: JevUsage


class JevResponseError(RuntimeError):
    """Raised when a successful API response violates the expected question contract."""


class InsufficientEvidenceError(RuntimeError):
    """Raised by ``decide`` when Jev explicitly cannot produce a safe decision."""

    def __init__(self, assessment: JevDecisionAssessment) -> None:
        super().__init__("Jev reported insufficient evidence for a DecisionResult")
        self.assessment = assessment
