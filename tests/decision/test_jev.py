from __future__ import annotations

import asyncio
from collections.abc import Mapping

import pytest
from typesafe_sdk import ChoiceAnswer, JSONContent, Question, SystemOneResponse, Usage

from decision.jev import (
    JevResponseError,
    JevWorldStateEvaluator,
    PrototypeAssessment,
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


def _response(choice: str = "concerning_interaction") -> SystemOneResponse:
    return SystemOneResponse(
        model="jev-test-double",
        answers={
            "assessment": ChoiceAnswer(
                choice=choice,
                confidence=0.82,
                probabilities={
                    "no_clear_concern": 0.08,
                    "concerning_interaction": 0.82,
                    "insufficient_evidence": 0.10,
                },
            )
        },
        usage=Usage(input_tokens=25, output_tokens=4),
    )


def test_world_state_is_serialized_as_plain_json_data() -> None:
    state = world_state_to_json(make_world_state())

    assert state["source_id"] == "synthetic-camera"
    assert state["people"][0]["track_id"] == 1
    assert state["people"][0]["person_fallen"] is None
    assert state["interactions"][0]["possible_contact"] is True
    assert state["interactions"][0]["repeated_aggressive_motion"] is None


def test_evaluator_sends_world_state_and_detaches_sdk_output() -> None:
    client = FakeJevClient(_response())

    output = asyncio.run(JevWorldStateEvaluator(client).evaluate(make_world_state()))

    assert client.state == {"worldState": world_state_to_json(make_world_state())}
    assert client.questions is not None
    assert set(client.questions) == {"assessment"}
    assert client.timeout == 10.0
    assert output.assessment is PrototypeAssessment.CONCERNING_INTERACTION
    assert output.confidence == 0.82
    assert output.model == "jev-test-double"
    assert output.usage.input_tokens == 25


def test_api_failure_is_not_converted_into_a_normal_assessment() -> None:
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
        asyncio.run(JevWorldStateEvaluator(FailingClient()).evaluate(make_world_state()))


def test_unknown_choice_is_rejected_as_an_invalid_response() -> None:
    with pytest.raises(JevResponseError, match="unknown assessment"):
        asyncio.run(JevWorldStateEvaluator(FakeJevClient(_response("unexpected"))).evaluate(
            make_world_state()
        ))
