"""Typed Jev questions for the first fight-detection MVP."""

from __future__ import annotations

from typesafe_sdk import Choice, Question


def build_mvp_questions() -> dict[str, Question]:
    """Return independent judgments over the same observable ``world_state`` evidence."""

    evidence_rule = (
        "Use only world_state. A null is unknown, never zero or false. Do not invent visual "
        "facts. Judge the temporal window as a whole. Recent peak motion and minimum proximity "
        "are intentionally retained so brief strikes are not lost between evaluations. "
        "Proximity, a small distance, bounding-box overlap, or time spent close are not aggression "
        "by themselves, even when boxes overlap strongly. Treat people who are merely standing, "
        "talking, walking together, hugging, or passing close as NORMAL when there is no dynamic "
        "corroboration. Person-level arm speed or acceleration, even when extreme, is not threat "
        "evidence by itself: it may be gesturing, exercise, or movement away from the other person. "
        "Never combine an independent recent arm-speed peak with an independent recent minimum "
        "wrist distance to invent a strike. Dynamic corroboration means rapid body approach, "
        "directionally correlated possible_contact, repeated close-contact motion, or a newly "
        "fallen-looking pose "
        "combined with abrupt nearby interaction. possible_contact is motion-gated, but remains "
        "evidence rather than proof. Rapid approach alone is ambiguous and can be a greeting or "
        "hug. A single smooth reciprocal reach toward both torsos that settles without repeated "
        "impact, head-directed contact, a fall, or abrupt instability is consistent with a hug "
        "and should be NORMAL. Treat pairwise_evidence_level APPROACH_ONLY or NONE_OR_NEGATIVE as "
        "non-violent unless an independently corroborated fall or repeated impact is present. A "
        "pairwise_evidence_level SINGLE_HEAD_STRIKE is already sufficient observable evidence for "
        "a one-sided ASSAULT even when it occurs only once; do not require repetition. A "
        "fallen-looking pose alone does not prove violence."
    )
    return {
        "evidence_quality": Choice(
            instructions=f"{evidence_rule} Is the evidence sufficient for an incident decision?",
            criteria={
                "SUFFICIENT": (
                    "There are enough observed signals to distinguish a normal interaction from "
                    "the listed concerning events. Well-observed low/static motion is sufficient "
                    "to decide NORMAL. A rapid approach, a motion-gated possible contact, repeated "
                    "aggressive motion, or a fall with abrupt nearby interaction can support a "
                    "concerning decision."
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
                "NORMAL": (
                    "Ordinary movement or interaction without dynamic aggression evidence. This "
                    "includes people standing very close, overlapping in 2D, talking, walking "
                    "together, passing, or hugging. A smooth reciprocal torso embrace remains "
                    "NORMAL when head-directed motion-gated contact, repeated aggressive motion, and a "
                    "corroborated fall are absent; rapid approach alone does not change that."
                ),
                "SUSPICIOUS_INTERACTION": (
                    "A sudden forceful approach corroborated by a motion-gated fast wrist contact, "
                    "or a fall accompanied by abrupt nearby interaction, but without enough "
                    "evidence for a coherent fight or one-sided assault. Rapid approach alone or "
                    "a smooth reciprocal torso embrace does not satisfy this criterion."
                ),
                "FIGHT": (
                    "Reciprocal or repeated aggressive physical exchange, especially repeated "
                    "close-contact arm motion involving both people."
                ),
                "ASSAULT": (
                    "Apparently one-sided physical aggression, including a fast hand movement "
                    "that reaches another person's head even if it is a single brief strike. "
                    "SINGLE_HEAD_STRIKE should select this event unless stronger reciprocal or "
                    "repeated evidence supports FIGHT."
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
                "HIGH": (
                    "Strong evidence of dangerous physical conflict or likely harm, including one "
                    "high-speed SINGLE_HEAD_STRIKE."
                ),
                "CRITICAL": "Immediate risk of severe harm, incapacitation, or ongoing attack.",
            },
        ),
        "urgency": Choice(
            instructions=f"{evidence_rule} How quickly should campus safety react?",
            criteria={
                "LOW": (
                    "No prompt reaction is indicated; static proximity or box overlap alone stays "
                    "at this level."
                ),
                "MEDIUM": "Review or monitor soon; immediate intervention is not yet clear.",
                "HIGH": (
                    "Prompt human attention or intervention is indicated, including for one "
                    "SINGLE_HEAD_STRIKE even without repetition."
                ),
                "CRITICAL": "Immediate intervention is indicated to reduce imminent danger.",
            },
        ),
        "action": Choice(
            instructions=(
                f"{evidence_rule} What is the proportionate recommendation? This is advisory "
                "only and does not execute any external action."
            ),
            criteria={
                "IGNORE": (
                    "No safety response is warranted; use this for normal static proximity or "
                    "overlap without dynamic aggression evidence."
                ),
                "MONITOR": "Continue observation or request human review.",
                "ALERT": (
                    "Notify a responsible operator promptly for assessment; this is the minimum "
                    "response for a SINGLE_HEAD_STRIKE."
                ),
                "DISPATCH_SECURITY": "Recommend immediate campus security intervention.",
            },
        ),
    }


def build_prototype_questions() -> dict[str, Question]:
    """Backward-compatible name for callers of the earlier prototype."""

    return build_mvp_questions()
