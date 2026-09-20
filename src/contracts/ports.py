"""Minimal callable boundaries that allow modules to be developed independently."""

from __future__ import annotations

from typing import Protocol

from .decision import DecisionResult
from .perception import PerceptionFrame
from .world_state import WorldState


class FeaturePipeline(Protocol):
    """Consumes frames continuously and emits a state only when one is ready."""

    def update(self, frame: PerceptionFrame) -> WorldState | None: ...


class DecisionEngine(Protocol):
    """Asynchronously maps one world state to a project decision."""

    async def decide(self, world_state: WorldState) -> DecisionResult: ...
