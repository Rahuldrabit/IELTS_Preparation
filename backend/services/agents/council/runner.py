"""
Council Runner — orchestrates the full multi-agent evaluation pipeline.

Architecture:
  Phase 1: Run LexicalTracker, SyntaxAuditor, RhetoricCohesion in PARALLEL.
  Phase 2: Feed all three verdicts to ChiefExaminer (sequential — needs all three).

This is the ONLY file that imports multiple council agents. All other code
imports only from here, keeping the coupling contained.
"""
import asyncio
import logging
from typing import Optional
from pydantic import BaseModel

from services.agents.council.lexical_tracker import LexicalTrackerAgent, LexicalVerdict
from services.agents.council.syntax_auditor import SyntaxAuditorAgent, SyntaxVerdict
from services.agents.council.rhetoric_cohesion import RhetoricCohesionAgent, CohesionVerdict
from services.agents.council.chief_examiner import ChiefExaminerAgent, ChiefExaminerVerdict

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Full report schema (returned to callers)
# ─────────────────────────────────────────────

class CouncilReport(BaseModel):
    """Complete Council of Judges output. Serialises cleanly to JSON."""
    lexical:  LexicalVerdict
    syntax:   SyntaxVerdict
    cohesion: CohesionVerdict
    chief:    ChiefExaminerVerdict


# ─────────────────────────────────────────────
#  Orchestrator
# ─────────────────────────────────────────────

async def run_council(
    essay: str,
    task_type: str = "task_2",
    task_prompt: Optional[str] = None,
    target_band: float = 7.0,
) -> CouncilReport:
    """
    Run the full Council of Judges pipeline.

    Phase 1 (parallel):  LexicalTracker + SyntaxAuditor + RhetoricCohesion
    Phase 2 (sequential): ChiefExaminer (depends on all three Phase 1 outputs)

    Raises GemmaClientError if any agent call fails.
    Callers should catch GemmaClientError and fall back to single-agent scoring.
    """
    logger.info("Council: starting evaluation (task_type=%s, target_band=%s)", task_type, target_band)

    # ── Phase 1: parallel ────────────────────────────────
    lexical_agent  = LexicalTrackerAgent()
    syntax_agent   = SyntaxAuditorAgent()
    cohesion_agent = RhetoricCohesionAgent()

    lexical_result, syntax_result, cohesion_result = await asyncio.gather(
        lexical_agent.evaluate(essay, task_type),
        syntax_agent.evaluate(essay, task_type),
        cohesion_agent.evaluate(essay, task_type, task_prompt),
    )

    logger.info(
        "Council Phase 1 complete: lexical=%.1f, syntax=%.1f, cohesion=%.1f",
        lexical_result.band, syntax_result.band, cohesion_result.band,
    )

    # ── Phase 2: Chief Examiner ──────────────────────────
    chief_agent   = ChiefExaminerAgent()
    chief_result  = await chief_agent.reconcile(
        lexical_result, syntax_result, cohesion_result, target_band
    )

    logger.info("Council Phase 2 complete: overall_band=%.1f", chief_result.overall_band)

    return CouncilReport(
        lexical=lexical_result,
        syntax=syntax_result,
        cohesion=cohesion_result,
        chief=chief_result,
    )
