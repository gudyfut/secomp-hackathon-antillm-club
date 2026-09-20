"""Async adapter from ``WorldState`` to a project-owned Jev assessment."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from typesafe_sdk import AsyncTypeSafeClient, JSONContent, Question, SystemOneResponse

from contracts import WorldState

from .questions import build_prototype_questions
from .serialization import build_jev_state
from .types import (
    JevAssessment,
    JevResponseError,
    JevUsage,
    PrototypeAssessment,
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


class JevWorldStateEvaluator:
    """Evaluate one temporal state without defining the final incident policy yet."""

    def __init__(self, client: AsyncJevClient, *, timeout_seconds: float = 10.0) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def evaluate(self, world_state: WorldState) -> JevAssessment:
        """Send the state to Jev and detach the typed answer from SDK objects."""

        response = await self._client.system_one(
            build_jev_state(world_state),
            build_prototype_questions(),
            timeout=self._timeout_seconds,
        )
        answer = response.choices.get("assessment")
        if answer is None:
            raise JevResponseError("Jev response is missing the 'assessment' Choice answer")
        try:
            assessment = PrototypeAssessment(answer.choice)
        except ValueError as error:
            raise JevResponseError(
                f"Jev returned an unknown assessment choice: {answer.choice!r}"
            ) from error

        return JevAssessment(
            assessment=assessment,
            confidence=answer.confidence,
            probabilities=dict(answer.probabilities),
            model=response.model,
            usage=JevUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
        )


def create_typesafe_client() -> AsyncTypeSafeClient:
    """Create the official async client, which reads ``TYPESAFE_API_KEY``."""

    return AsyncTypeSafeClient()
