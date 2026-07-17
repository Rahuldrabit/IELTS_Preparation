"""
Agents Router — all agent HTTP endpoints in one place.

Each endpoint is a thin FastAPI handler that:
  1. Validates the request payload (Pydantic)
  2. Calls the appropriate agent
  3. Returns the structured result

No business logic lives here. Every LLM call is inside an agent class.

Mount in the main app:
    from services.agents.router import router as agents_router
    app.include_router(agents_router)
"""
import os
import tempfile
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from services.ai_agent.gemma_client import GemmaClientError
from services.agents.council import run_council, CouncilReport
from services.agents.socratic import SocraticHintAgent, SocraticHintRequest, SocraticHintResponse
from services.agents.syllabus import SyllabusCuratorAgent, SkillTelemetrySummary, UmaIntervention
from services.agents.adversarial import (
    AdversarialDistractorAgent,
    AdversarialGenerationRequest,
    AdversarialQuestionSet,
    StudentWeaknessProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


# ─────────────────────────────────────────────
#  Council of Judges
# ─────────────────────────────────────────────

class CouncilEvalRequest(BaseModel):
    essay: str
    task_type: str = "task_2"
    task_prompt: Optional[str] = None
    target_band: float = 7.0


@router.post("/council/evaluate", response_model=CouncilReport)
async def council_evaluate(request: CouncilEvalRequest):
    """
    Run the full Council of Judges multi-agent evaluation.

    Phase 1 (parallel): LexicalTracker + SyntaxAuditor + RhetoricCohesion
    Phase 2: ChiefExaminer reconciles → final band scores + improvements
    """
    try:
        return await run_council(
            essay=request.essay,
            task_type=request.task_type,
            task_prompt=request.task_prompt,
            target_band=request.target_band,
        )
    except GemmaClientError as e:
        logger.error("Council evaluation failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected council error")
        raise HTTPException(status_code=500, detail=f"Council evaluation failed: {str(e)}")


# ─────────────────────────────────────────────
#  Socratic Debugging Agent
# ─────────────────────────────────────────────

@router.post("/socratic/hint", response_model=SocraticHintResponse)
async def socratic_hint(request: SocraticHintRequest):
    """
    Get the next Socratic guiding question for a wrong reading answer.

    Pass the conversation_history to maintain the multi-turn dialogue.
    Hint level is derived automatically from history length.
    """
    agent = SocraticHintAgent()
    try:
        return await agent.get_hint(request)
    except GemmaClientError as e:
        logger.error("Socratic hint failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected socratic error")
        raise HTTPException(status_code=500, detail=f"Hint generation failed: {str(e)}")


# ─────────────────────────────────────────────
#  Autonomous Syllabus Curating Agent
# ─────────────────────────────────────────────

@router.post("/syllabus/analyse", response_model=UmaIntervention)
async def syllabus_analyse(telemetry: SkillTelemetrySummary):
    """
    Run the Autonomous Syllabus Curating Agent against fresh telemetry.
    Returns Uma's intervention: headline, insight, prioritised tasks, drill spec.

    Typically called fire-and-forget after session submission.
    Result should be stored in user.ava_intervention.
    """
    agent = SyllabusCuratorAgent()
    try:
        return await agent.analyse(telemetry)
    except GemmaClientError as e:
        logger.error("Syllabus analysis failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected syllabus error")
        raise HTTPException(status_code=500, detail=f"Syllabus analysis failed: {str(e)}")


# ─────────────────────────────────────────────
#  Adversarial Distractor Agent
# ─────────────────────────────────────────────

@router.post("/adversarial/generate", response_model=AdversarialQuestionSet)
async def adversarial_generate(request: AdversarialGenerationRequest):
    """
    Generate a targeted adversarial reading set.

    The question set is designed to expose the student's specific cognitive
    blind spots — negative qualifiers, synonym traps, partial truths, etc.
    Each question is tagged with a trap_type for the review panel.
    """
    agent = AdversarialDistractorAgent()
    try:
        return await agent.generate(request)
    except GemmaClientError as e:
        logger.error("Adversarial generation failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected adversarial error")
        raise HTTPException(status_code=500, detail=f"Adversarial generation failed: {str(e)}")
