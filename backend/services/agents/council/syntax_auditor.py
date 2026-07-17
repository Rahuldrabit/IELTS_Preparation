"""
SyntaxAuditorAgent — IELTS grammar and sentence structure specialist.

Evaluates grammatical range, structural complexity, punctuation, and tense
stability. Does NOT evaluate vocabulary or argument quality.
"""
from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry


# ─────────────────────────────────────────────
#  Output schema
# ─────────────────────────────────────────────

class SyntaxVerdict(BaseModel):
    band: float
    dominant_structure: str                   # "Simple S-V-O" | "Mixed" | "Complex"
    grammar_errors: list[str]                 # Up to 3 specific error examples (quote from essay)
    advanced_structures_found: list[str]      # Relative clauses, passives, conditionals, etc.
    explanation: str


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class SyntaxAuditorAgent(BaseAgent):
    name = "SyntaxAuditorAgent"
    description = "Evaluates IELTS grammar range, structural complexity, and error rate."

    def _build_prompt(self, essay: str, task_type: str) -> str:
        return f"""You are the SYNTAX AUDITOR AGENT on an IELTS examining committee.
Your ONLY job is to evaluate grammar and sentence structure.
Do not comment on vocabulary choices or argument quality.

ESSAY ({task_type.replace('_', ' ').upper()}):
{essay[:2500]}

Evaluate:
1. Overall grammar band (1.0–9.0)
2. Dominant sentence structure: Simple S-V-O | Mixed | Complex
3. Specific grammar errors — quote exact text from the essay, up to 3
4. Advanced structures correctly used (relative clauses, passive voice, conditionals,
   inverted conditionals, gerund/infinitive contrasts, etc.) — list up to 4
5. 2–3 sentence explanation of the band score

Return JSON matching SyntaxVerdict schema exactly. No commentary outside the JSON."""

    async def evaluate(self, essay: str, task_type: str = "task_2") -> SyntaxVerdict:
        return await self.run_structured(
            prompt=self._build_prompt(essay, task_type),
            schema=SyntaxVerdict,
            temperature=0.1,
        )
