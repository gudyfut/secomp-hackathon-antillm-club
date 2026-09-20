"""Provisional Jev questions, isolated for later MVP calibration."""

from __future__ import annotations

from typesafe_sdk import Choice, Question


def build_prototype_questions() -> dict[str, Question]:
    """Return a fresh question mapping for the current connectivity prototype."""

    return {
        "assessment": Choice(
            instructions=(
                "Considerando somente os sinais em `worldState`, qual opcao melhor descreve "
                "a evidencia sobre uma interacao preocupante? Nao presuma valores para campos "
                "nulos e nao trate ausencia de evidencia como uma interacao normal."
            ),
            criteria={
                "no_clear_concern": (
                    "Os sinais disponiveis nao mostram evidencia clara de uma interacao "
                    "preocupante."
                ),
                "concerning_interaction": (
                    "Os sinais disponiveis mostram evidencia de uma interacao que merece "
                    "atencao."
                ),
                "insufficient_evidence": (
                    "Os sinais sao ausentes, incompletos ou ambiguos demais para esse julgamento."
                ),
            },
        )
    }
