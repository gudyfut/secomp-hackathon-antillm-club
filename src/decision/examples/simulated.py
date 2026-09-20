"""Offline Jev simulation showing input, request, response and mapped output."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

from typesafe_sdk import (
    ChoiceAnswer,
    JSONContent,
    Question,
    SystemOneResponse,
    Usage,
)

from decision.examples.common import make_example_world_state, print_json
from decision.jev import JevWorldStateEvaluator


class SimulatedJevClient:
    """Deterministic test double; it never performs a network request."""

    def __init__(self) -> None:
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
        return SystemOneResponse(
            model="jev-simulated",
            answers={
                "assessment": ChoiceAnswer(
                    choice="concerning_interaction",
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


async def main() -> None:
    world_state = make_example_world_state()
    client = SimulatedJevClient()
    evaluator = JevWorldStateEvaluator(client)

    print_json("1. WORLDSTATE RECEBIDO", world_state)
    result = await evaluator.evaluate(world_state)
    print_json("2. STATE JSON QUE SERIA ENVIADO AO JEV", client.state)
    print_json("3. QUESTIONS QUE SERIAM ENVIADAS AO JEV", client.questions)
    print_json("4. RESPOSTA SIMULADA MAPEADA", result)
    print("\nRESULTADO: simulacao concluida sem rede e sem consumir a API.")


if __name__ == "__main__":
    asyncio.run(main())
