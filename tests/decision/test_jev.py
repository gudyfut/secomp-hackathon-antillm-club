from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import replace

import pytest
from typesafe_sdk import ChoiceAnswer, JSONContent, Question, SystemOneResponse, Usage

from contracts import Action, EventType, InteractionFeatures, Severity, Urgency, WorldState
from decision.jev import (
    DecisionStatus,
    InsufficientEvidenceError,
    JevDecisionEngine,
    JevResponseError,
    WorldStatePayloadError,
    build_mvp_questions,
    world_state_to_json,
)
from tests.fixtures.synthetic import make_world_state


class FakeJevClient:
    def __init__(self, response: SystemOneResponse) -> None:
        self.response = response
        self.state: JSONContent | None = None
        self.questions: Mapping[str, Question] | None = None
        self.timeout: float | None = None

    async def system_one(
        self,
        state: JSONContent,
        questions: Mapping[str, Question],
        *,
        timeout: float | None = None,
    ) -> SystemOneResponse:
        self.state = state
        self.questions = questions
        self.timeout = timeout
        return self.response


def _answer(choice: str, *alternatives: str) -> ChoiceAnswer:
    probability = round(0.12 / len(alternatives), 4) if alternatives else 0.0
    return ChoiceAnswer(
        choice=choice,
        confidence=0.88,
        probabilities={choice: 0.88, **dict.fromkeys(alternatives, probability)},
    )


def _response(
    *,
    evidence_quality: str = "SUFFICIENT",
    event: str = "SUSPICIOUS_INTERACTION",
    omit: str | None = None,
) -> SystemOneResponse:
    answers = {
        "evidence_quality": _answer(evidence_quality, "INSUFFICIENT"),
        "event": _answer(event, "NORMAL", "FIGHT", "ASSAULT", "UNKNOWN_ANOMALY"),
        "severity": _answer("HIGH", "LOW", "MEDIUM", "CRITICAL"),
        "urgency": _answer("HIGH", "LOW", "MEDIUM", "CRITICAL"),
        "action": _answer("ALERT", "IGNORE", "MONITOR", "DISPATCH_SECURITY"),
    }
    if omit is not None:
        answers.pop(omit)
    return SystemOneResponse(
        model="jev-test-double",
        answers=answers,
        usage=Usage(input_tokens=120, output_tokens=15),
    )


def test_world_state_becomes_compact_semantic_jev_input() -> None:
    payload = world_state_to_json(make_world_state())

    assert payload["schema_version"] == "world-state.jev.v1"
    assert payload["observation_window"] == {"duration_ms": 1_000}
    assert payload["summary"] == {
        "people_count": 2,
        "interaction_count": 1,
        "available_signal_count": 9,
        "possible_signal_count": 18,
        "signal_coverage": 0.5,
    }
    assert "source_id" not in payload
    assert "observed_at_ms" not in payload
    assert payload["people"][0]["person_fallen"] is None
    interaction = payload["interactions"][0]
    assert interaction["possible_contact"] is True
    assert interaction["repeated_aggressive_motion"] is None
    assert "first_wrist_to_second_head_distance_body_heights" in interaction
    assert "wrist_to_head_distance" not in interaction


@pytest.mark.parametrize(
    ("state", "message"),
    [
        (replace(make_world_state(), window_start_ms=2_000), "window_end_ms must not precede"),
        (
            replace(
                make_world_state(),
                people=(make_world_state().people[0], make_world_state().people[0]),
            ),
            "unique track_id",
        ),
        (
            replace(
                make_world_state(),
                interactions=(InteractionFeatures(first_track_id=1, second_track_id=99),),
            ),
            "tracks present in people",
        ),
        (
            replace(
                make_world_state(),
                people=(replace(make_world_state().people[0], body_speed=float("nan")),),
                interactions=(),
            ),
            "body_speed must be finite",
        ),
    ],
)
def test_invalid_world_state_is_rejected_before_api(state: WorldState, message: str) -> None:
    with pytest.raises(WorldStatePayloadError, match=message):
        world_state_to_json(state)


def test_questions_cover_each_independent_decision_dimension() -> None:
    assert set(build_mvp_questions()) == {
        "evidence_quality",
        "event",
        "severity",
        "urgency",
        "action",
    }


def test_sufficient_response_maps_to_shared_decision_contract() -> None:
    client = FakeJevClient(_response())
    engine = JevDecisionEngine(client)

    assessment = asyncio.run(engine.evaluate(make_world_state()))
    decision = asyncio.run(engine.decide(make_world_state()))

    assert client.state is not None and "world_state" in client.state
    assert client.questions is not None and len(client.questions) == 5
    assert client.timeout == 10.0
    assert assessment.status is DecisionStatus.DECIDED
    assert assessment.decision is not None
    assert assessment.decision.event is EventType.SUSPICIOUS_INTERACTION
    assert assessment.decision.severity is Severity.HIGH
    assert assessment.decision.urgency is Urgency.HIGH
    assert assessment.decision.action is Action.ALERT
    assert assessment.decision.world_state_observed_at_ms == 1_000
    assert assessment.evidence_quality.confidence == 0.88
    assert assessment.model == "jev-test-double"
    assert assessment.usage.input_tokens == 120
    assert decision == assessment.decision


def test_insufficient_evidence_is_never_converted_to_normal() -> None:
    engine = JevDecisionEngine(FakeJevClient(_response(evidence_quality="INSUFFICIENT")))

    assessment = asyncio.run(engine.evaluate(make_world_state()))

    assert assessment.status is DecisionStatus.INSUFFICIENT_EVIDENCE
    assert assessment.decision is None
    with pytest.raises(InsufficientEvidenceError) as caught:
        asyncio.run(engine.decide(make_world_state()))
    assert caught.value.assessment.status is DecisionStatus.INSUFFICIENT_EVIDENCE


def test_api_failure_is_not_converted_into_a_decision() -> None:
    class FailingClient:
        async def system_one(
            self,
            state: JSONContent,
            questions: Mapping[str, Question],
            *,
            timeout: float | None = None,
        ) -> SystemOneResponse:
            raise RuntimeError("simulated API failure")

    with pytest.raises(RuntimeError, match="simulated API failure"):
        asyncio.run(JevDecisionEngine(FailingClient()).evaluate(make_world_state()))


def test_missing_answer_is_rejected_as_invalid_response() -> None:
    with pytest.raises(JevResponseError, match="missing the 'urgency'"):
        asyncio.run(
            JevDecisionEngine(FakeJevClient(_response(omit="urgency"))).evaluate(
                make_world_state()
            )
        )


def test_unknown_choice_is_rejected_as_invalid_response() -> None:
    with pytest.raises(JevResponseError, match="unknown event"):
        asyncio.run(
            JevDecisionEngine(FakeJevClient(_response(event="UNEXPECTED"))).evaluate(
                make_world_state()
            )
        )
