"""Adversarial Distractor Agent — re-exports."""
from services.agents.adversarial.distractor import (
    AdversarialDistractorAgent,
    AdversarialGenerationRequest,
    AdversarialQuestionSet,
    AdversarialQuestion,
    StudentWeaknessProfile,
    TrapType,
    TRAP_DESCRIPTIONS,
)

__all__ = [
    "AdversarialDistractorAgent",
    "AdversarialGenerationRequest",
    "AdversarialQuestionSet",
    "AdversarialQuestion",
    "StudentWeaknessProfile",
    "TrapType",
    "TRAP_DESCRIPTIONS",
]
