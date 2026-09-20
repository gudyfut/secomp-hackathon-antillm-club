"""Typed Jev questions for the first fight-detection MVP."""

from __future__ import annotations

from typesafe_sdk import Choice, Question


def build_mvp_questions() -> dict[str, Question]:
    """Return independent judgments over the same observable ``world_state`` evidence."""

    evidence_rule = (
        "Use only world_state. A null is unknown, never zero or false. Do not invent visual "
        "facts. Judge the temporal window as a whole. Recent peak motion and minimum proximity "
        "are intentionally retained so brief strikes are not lost between evaluations."
    )
    return {
        "evidence_quality": Choice(
            instructions=f"{evidence_rule} Is the evidence sufficient for an incident decision?",
            criteria={
                "SUFFICIENT": (
                    "There are enough motion or interaction signals to distinguish the listed "
                    "event classes. A rapid arm-motion peak combined with probable wrist contact "
                    "or very small wrist-to-head/torso distance can be sufficient by itself."
                ),
                "INSUFFICIENT": (
                    "Signals are absent, too sparse, contradictory, or too ambiguous for a "
                    "reliable event judgment."
                ),
            },
        ),
        "event": Choice(
            instructions=f"{evidence_rule} Which event best describes the observable evidence?",
            criteria={
                "NORMAL": "Ordinary movement or interaction with no clear safety concern.",
                "SUSPICIOUS_INTERACTION": (
                    "Concerning rapid approach, close wrist-to-head/torso motion, probable "
                    "contact, or a strong arm-motion peak, but not a coherent fight or assault."
                ),
                "FIGHT": (
                    "Reciprocal or repeated aggressive physical exchange, especially repeated "
                    "close-contact arm motion involving both people."
                ),
                "ASSAULT": (
                    "Apparently one-sided physical aggression, including a fast hand movement "
                    "that reaches another person's head or torso even if it is brief."
                ),
                "UNKNOWN_ANOMALY": (
                    "A concerning observable pattern that does not fit the other event classes."
                ),
            },
        ),
        "severity": Choice(
            instructions=(
                f"{evidence_rule} How serious is the apparent harm or danger in this window?"
            ),
            criteria={
                "LOW": "No apparent harm or only a weak concern.",
                "MEDIUM": "Credible concern with limited apparent harm or escalation.",
                "HIGH": "Strong evidence of dangerous physical conflict or likely harm.",
                "CRITICAL": "Immediate risk of severe harm, incapacitation, or ongoing attack.",
            },
        ),
        "urgency": Choice(
            instructions=f"{evidence_rule} How quickly should campus safety react?",
            criteria={
                "LOW": "No prompt reaction is indicated.",
                "MEDIUM": "Review or monitor soon; immediate intervention is not yet clear.",
                "HIGH": "Prompt human attention or intervention is indicated.",
                "CRITICAL": "Immediate intervention is indicated to reduce imminent danger.",
            },
        ),
        "action": Choice(
            instructions=(
                f"{evidence_rule} What is the proportionate recommendation? This is advisory "
                "only and does not execute any external action."
            ),
            criteria={
                "IGNORE": "No safety response is warranted from the available evidence.",
                "MONITOR": "Continue observation or request human review.",
                "ALERT": "Notify a responsible operator promptly for assessment.",
                "DISPATCH_SECURITY": "Recommend immediate campus security intervention.",
            },
        ),
    }


def build_prototype_questions() -> dict[str, Question]:
    """Backward-compatible name for callers of the earlier prototype."""

    return build_mvp_questions()
