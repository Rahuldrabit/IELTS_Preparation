"""
RhetoricCohesionAgent — IELTS paragraph structure and task response specialist.

Evaluates transition quality, logical argument flow, cohesive device usage,
and completeness of task response. Does NOT evaluate individual grammar errors
or vocabulary choices.
"""
from typing import Optional
from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry


# ─────────────────────────────────────────────
#  Output schema
# ─────────────────────────────────────────────

class CohesionVerdict(BaseModel):
    band: float
    task_response_score: float              # How fully does it address all parts? (1–9)
    cohesive_devices_used: list[str]        # "However", "In addition", etc. (up to 5)
    paragraph_structure: str               # "Clear" | "Weak" | "Missing"
    logical_gaps: list[str]                 # Up to 2 reasoning gaps identified
    explanation: str


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class RhetoricCohesionAgent(BaseAgent):
    name = "RhetoricCohesionAgent"
    description = "Evaluates IELTS task response completeness, paragraph transitions, and argument logic."

    def _build_prompt(
        self,
        essay: str,
        task_type: str,
        task_prompt: Optional[str],
    ) -> str:
        task_context = (
            f"\n\nORIGINAL TASK PROMPT:\n{task_prompt}"
            if task_prompt else ""
        )
        return f"""You are the RHETORIC & COHESION AGENT on an IELTS examining committee.
Your ONLY job is to evaluate paragraph organisation, transitions, and task response completeness.
Do not comment on vocabulary choices or individual grammar errors.

ESSAY ({task_type.replace('_', ' ').upper()}):
{essay[:2500]}{task_context}

Evaluate:
1. Overall coherence/cohesion band (1.0–9.0)
2. Task response score separately (1.0–9.0) — does it address ALL parts of the task?
3. Cohesive devices and discourse markers used — list up to 5 actual examples from the essay
4. Paragraph structure quality: Clear | Weak | Missing
5. Logical reasoning gaps — name up to 2 specific missing arguments or unsupported claims
6. 2–3 sentence explanation of the band score

Return JSON matching CohesionVerdict schema exactly. No commentary outside the JSON."""

    async def evaluate(
        self,
        essay: str,
        task_type: str = "task_2",
        task_prompt: Optional[str] = None,
    ) -> CohesionVerdict:
        return await self.run_structured(
            prompt=self._build_prompt(essay, task_type, task_prompt),
            schema=CohesionVerdict,
            temperature=0.1,
        )
