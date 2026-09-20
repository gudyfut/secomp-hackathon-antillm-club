"""Async adapter from ``WorldState`` to a project-owned decision."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Protocol, TypeVar

from typesafe_sdk import AsyncTypeSafeClient, JSONContent, Question, SystemOneResponse

from contracts import Action, DecisionResult, EventType, Severity, Urgency, WorldState

from .questions import build_mvp_questions
from .serialization import build_jev_state
from .types import (
    ChoiceJudgment,
    DecisionStatus,
    InsufficientEvidenceError,
    JevDecisionAssessment,
    JevResponseError,
    JevUsage,
)


class AsyncJevClient(Protocol):
    """Small injectable SDK surface used by production and offline tests."""

    async def system_one(
        self,
        state: JSONContent,
        questions: Mapping[str, Question],
        *,
        timeout: float | None = None,
    ) -> SystemOneResponse: ...


_EnumT = TypeVar("_EnumT", bound=StrEnum)


def _choice(response: SystemOneResponse, question_id: str) -> ChoiceJudgment:
    answer = response.choices.get(question_id)
    if answer is None:
        raise JevResponseError(f"Jev response is missing the {question_id!r} Choice answer")
    return ChoiceJudgment(
        choice=answer.choice,
        confidence=answer.confidence,
        probabilities=dict(answer.probabilities),
    )


def _enum(judgment: ChoiceJudgment, enum_type: type[_EnumT], question_id: str) -> _EnumT:
    try:
        return enum_type(judgment.choice)
    except ValueError as error:
        raise JevResponseError(
            f"Jev returned an unknown {question_id} choice: {judgment.choice!r}"
        ) from error


class JevDecisionEngine:
    """Ask Jev for typed contextual judgments over one temporal evidence window."""

    def __init__(self, client: AsyncJevClient, *, timeout_seconds: float = 10.0) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def evaluate(self, world_state: WorldState) -> JevDecisionAssessment:
        """Return all judgments and telemetry without hiding insufficient evidence."""

        response = await self._client.system_one(
            build_jev_state(world_state),
            build_mvp_questions(),
            timeout=self._timeout_seconds,
        )
        evidence_quality = _choice(response, "evidence_quality")
        event = _choice(response, "event")
        severity = _choice(response, "severity")
        urgency = _choice(response, "urgency")
        action = _choice(response, "action")

        if evidence_quality.choice == "INSUFFICIENT":
            status = DecisionStatus.INSUFFICIENT_EVIDENCE
            decision = None
        elif evidence_quality.choice == "SUFFICIENT":
            status = DecisionStatus.DECIDED
            decision = DecisionResult(
                event=_enum(event, EventType, "event"),
                severity=_enum(severity, Severity, "severity"),
                urgency=_enum(urgency, Urgency, "urgency"),
                action=_enum(action, Action, "action"),
                world_state_observed_at_ms=world_state.observed_at_ms,
                rationale_codes=("JEV_MVP_V1",),
            )
        else:
            raise JevResponseError(
                "Jev returned an unknown evidence_quality choice: "
                f"{evidence_quality.choice!r}"
            )

        return JevDecisionAssessment(
            status=status,
            decision=decision,
            evidence_quality=evidence_quality,
            event=event,
            severity=severity,
            urgency=urgency,
            action=action,
            world_state_observed_at_ms=world_state.observed_at_ms,
            model=response.model,
            usage=JevUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
        )

    async def decide(self, world_state: WorldState) -> DecisionResult:
        """Implement the shared DecisionEngine port for states with sufficient evidence."""

        assessment = await self.evaluate(world_state)
        if assessment.decision is None:
            raise InsufficientEvidenceError(assessment)
        return assessment.decision


# Temporary alias so existing local scripts keep working while the MVP name changes.
JevWorldStateEvaluator = JevDecisionEngine


def create_typesafe_client() -> AsyncTypeSafeClient:
    """Create the official async client, which reads ``TYPESAFE_API_KEY``."""

    return AsyncTypeSafeClient()
