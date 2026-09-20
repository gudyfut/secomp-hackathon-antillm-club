"""Stable, dependency-free contracts shared by Campus Sentinel modules."""

from .decision import Action, DecisionResult, EventType, Severity, Urgency
from .perception import BoundingBox, PerceptionFrame, PoseKeypoint, PoseKeypoints, TrackedPerson
from .ports import DecisionEngine, FeaturePipeline
from .world_state import InteractionFeatures, PersonFeatures, WorldState

__all__ = [
    "Action",
    "BoundingBox",
    "DecisionEngine",
    "DecisionResult",
    "EventType",
    "FeaturePipeline",
    "InteractionFeatures",
    "PerceptionFrame",
    "PersonFeatures",
    "PoseKeypoint",
    "PoseKeypoints",
    "Severity",
    "TrackedPerson",
    "Urgency",
    "WorldState",
]
