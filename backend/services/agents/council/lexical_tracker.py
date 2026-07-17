"""
LexicalTrackerAgent — IELTS vocabulary specialist.

Scans only for vocabulary depth, CEFR level, collocations, and repetition.
Does NOT evaluate grammar or argument structure.
"""
from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry


# ─────────────────────────────────────────────
#  Output schema
# ─────────────────────────────────────────────

class LexicalVerdict(BaseModel):
    band: float                       # 1.0–9.0
    cefr_level_detected: str          # A2 | B1 | B2 | C1 | C2
    repetition_offenders: list[str]   # Most overused words (up to 5)
    strong_collocations: list[str]    # Good vocabulary choices found (up to 4)
    weak_vocabulary: list[str]        # Simple/misused words to upgrade (up to 4)
    explanation: str                  # 2–3 sentence rationale for the band


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class LexicalTrackerAgent(BaseAgent):
    name = "LexicalTrackerAgent"
    description = "Evaluates IELTS vocabulary depth, CEFR level, collocations, and repetition."

    def _build_prompt(self, essay: str, task_type: str) -> str:
        return f"""You are the LEXICAL TRACKER AGENT on an IELTS examining committee.
Your ONLY job is to evaluate vocabulary. Do not comment on grammar or argument structure.

ESSAY ({task_type.replace('_', ' ').upper()}):
{essay[:2500]}

Evaluate:
1. Overall vocabulary band (1.0–9.0)
2. Estimated CEFR level of the writing (A2 / B1 / B2 / C1 / C2)
3. Words/phrases repeated excessively — list up to 5
4. Strong, accurate collocations you found — list up to 4
5. Simple or misused words that should be upgraded — list up to 4
6. 2–3 sentence explanation of the band score

Return JSON matching LexicalVerdict schema exactly. No commentary outside the JSON."""

    async def evaluate(self, essay: str, task_type: str = "task_2") -> LexicalVerdict:
        return await self.run_structured(
            prompt=self._build_prompt(essay, task_type),
            schema=LexicalVerdict,
            temperature=0.1,
        )
