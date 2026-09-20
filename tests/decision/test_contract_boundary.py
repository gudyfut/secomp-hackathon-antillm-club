import asyncio

from contracts import (
    Action,
    DecisionEngine,
    DecisionResult,
    EventType,
    Severity,
    Urgency,
    WorldState,
)
from tests.fixtures.synthetic import make_world_state


class SyntheticDecisionEngine:
    async def decide(self, world_state: WorldState) -> DecisionResult:
        return DecisionResult(
            event=EventType.SUSPICIOUS_INTERACTION,
            severity=Severity.MEDIUM,
            urgency=Urgency.MEDIUM,
            action=Action.MONITOR,
            world_state_observed_at_ms=world_state.observed_at_ms,
            rationale_codes=("SYNTHETIC_TEST",),
        )


def test_decision_engine_can_be_developed_with_synthetic_world_state() -> None:
    engine: DecisionEngine = SyntheticDecisionEngine()

    result = asyncio.run(engine.decide(make_world_state()))

    assert result.action is Action.MONITOR
    assert result.world_state_observed_at_ms == 1_000
