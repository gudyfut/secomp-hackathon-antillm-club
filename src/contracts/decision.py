"""Stable decision vocabulary exposed to the interface."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EventType(StrEnum):
    NORMAL = "NORMAL"
    SUSPICIOUS_INTERACTION = "SUSPICIOUS_INTERACTION"
    FIGHT = "FIGHT"
    ASSAULT = "ASSAULT"
    UNKNOWN_ANOMALY = "UNKNOWN_ANOMALY"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Urgency(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Action(StrEnum):
    IGNORE = "IGNORE"
    MONITOR = "MONITOR"
    ALERT = "ALERT"
    DISPATCH_SECURITY = "DISPATCH_SECURITY"


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """Project-owned decision output; it must not expose Jev SDK response objects."""

    event: EventType
    severity: Severity
    urgency: Urgency
    action: Action
    world_state_observed_at_ms: int
    rationale_codes: tuple[str, ...] = ()
