from datetime import date
from shared.models import User
from services.agents.profile import ProfileAgent
from .schemas import PersonalizedPlan

DEFAULT_FEATURES = {
    "reading":   {"telemetry": False, "confidenceFlags": False},
    "writing":   {"scaffoldMode": False, "liveEvaluation": False},
    "listening": {"acousticLevel": 1,   "telemetry": False},
    "speaking":  {"mutationEngine": False, "workletRecorder": False},
}


def merge_features(stored: dict) -> dict:
    result = {}
    for skill, defaults in DEFAULT_FEATURES.items():
        result[skill] = {**defaults, **(stored.get(skill) or {})}
    return result


async def generate_personalized_plan(user: User) -> PersonalizedPlan:
    agent = ProfileAgent()
    return await agent.generate_personalized_plan(user)
