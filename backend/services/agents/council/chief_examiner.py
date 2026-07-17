"""
ChiefExaminerAgent — conflict resolver and final band scorer.

Ingests the three sub-agent verdicts and reconciles any disagreements.
Applies official IELTS rounding rules (nearest 0.5) to produce the
four criterion scores and the overall band.
"""
from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry
from services.agents.council.lexical_tracker import LexicalVerdict
from services.agents.council.syntax_auditor import SyntaxVerdict
from services.agents.council.rhetoric_cohesion import CohesionVerdict


# ─────────────────────────────────────────────
#  Output schema
# ─────────────────────────────────────────────

class ChiefExaminerVerdict(BaseModel):
    overall_band: float
    task_response: float
    coherence: float
    lexical: float
    grammar: float
    reconciliation_note: str        # Only meaningful when sub-agents disagree >1.5 bands
    priority_improvements: list[str]  # Top 3 improvements across all criteria
    meets_target_band: bool


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class ChiefExaminerAgent(BaseAgent):
    name = "ChiefExaminerAgent"
    description = "Reconciles sub-agent verdicts and produces the final IELTS band score."

    def _build_prompt(
        self,
        lexical: LexicalVerdict,
        syntax: SyntaxVerdict,
        cohesion: CohesionVerdict,
        target_band: float,
    ) -> str:
        return f"""You are the CHIEF EXAMINER AGENT.
Three specialist agents have independently evaluated this IELTS essay.

LEXICAL TRACKER  → band={lexical.band}
{lexical.explanation}

SYNTAX AUDITOR   → band={syntax.band}
{syntax.explanation}

RHETORIC & COHESION → band={cohesion.band}  (task_response={cohesion.task_response_score})
{cohesion.explanation}

STUDENT TARGET BAND: {target_band}

Your responsibilities:
1. Calculate OFFICIAL IELTS band scores (each rounded to nearest 0.5):
   - Task Response          = cohesion.task_response_score
   - Coherence & Cohesion   = cohesion.band
   - Lexical Resource       = lexical.band
   - Grammatical Range      = syntax.band
   - Overall                = mean of all four (rounded to nearest 0.5)
2. If any two agents disagree by more than 1.5 bands, write a reconciliation_note
   explaining which verdict you weighted more and why.
   If there is no significant disagreement, set reconciliation_note to "".
3. List the top 3 prioritised improvements across ALL criteria (be specific).
4. Set meets_target_band = true ONLY if overall_band >= target_band - 0.25

Return JSON matching ChiefExaminerVerdict schema exactly. No commentary outside the JSON."""

    async def reconcile(
        self,
        lexical: LexicalVerdict,
        syntax: SyntaxVerdict,
        cohesion: CohesionVerdict,
        target_band: float = 7.0,
    ) -> ChiefExaminerVerdict:
        return await self.run_structured(
            prompt=self._build_prompt(lexical, syntax, cohesion, target_band),
            schema=ChiefExaminerVerdict,
            temperature=0.1,
        )
