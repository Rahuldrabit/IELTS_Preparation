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

from services.llm import LLMClientError
from services.agents.council import run_council, CouncilReport
from services.agents.socratic import SocraticHintAgent, SocraticHintRequest, SocraticHintResponse
from services.agents.syllabus import SyllabusCuratorAgent, SkillTelemetrySummary, UmaIntervention
from services.agents.adversarial import (
    AdversarialDistractorAgent,
    AdversarialGenerationRequest,
    AdversarialQuestionSet,
    StudentWeaknessProfile,
)
from services.agents.registry import registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


# ─────────────────────────────────────────────
#  Registry Inspection
# ─────────────────────────────────────────────

@router.get("/registry")
async def list_agents():
    """Return all agent names currently registered in the global AgentRegistry."""
    return {"agents": registry.all_names()}


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
    except LLMClientError as e:
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
    except LLMClientError as e:
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
    except LLMClientError as e:
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
    except LLMClientError as e:
        logger.error("Adversarial generation failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected adversarial error")
        raise HTTPException(status_code=500, detail=f"Adversarial generation failed: {str(e)}")


# ─────────────────────────────────────────────
#  Error DNA Agent
# ─────────────────────────────────────────────

from services.agents.error_dna import ErrorDNAAgent, ErrorDNAResult

class ErrorDNARequest(BaseModel):
    """Request for Error DNA analysis."""
    user_id: int
    period_days: int = 30  # How many days of history to analyze


class ErrorDNAProfileRequest(BaseModel):
    """Request with pre-computed error profile."""
    error_profile: dict  # CrossModuleErrorProfile as dict


@router.post("/error-dna/analyse", response_model=ErrorDNAResult)
async def error_dna_analyse(request: ErrorDNAProfileRequest):
    """
    Run Error DNA analysis on a pre-computed error profile.
    
    This endpoint accepts the error_profile directly (from the analytics aggregation layer).
    Returns identified error signatures with recommendations.
    
    For the full workflow, use /error-dna/analyse-user instead.
    """
    agent = ErrorDNAAgent()
    try:
        return await agent.analyse(request.error_profile)
    except LLMClientError as e:
        logger.error("Error DNA analysis failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error DNA error")
        raise HTTPException(status_code=500, detail=f"Error DNA analysis failed: {str(e)}")


@router.post("/error-dna/analyse-user")
async def error_dna_analyse_user(request: ErrorDNARequest):
    """
    Run full Error DNA analysis for a user.
    
    This endpoint:
    1. Fetches the cross-module error profile from the analytics layer
    2. Runs the Error DNA agent to identify signatures
    3. Returns the full analysis
    
    Note: Does NOT persist the results. Use the weekly job or manual save for persistence.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from shared.database import get_db
    from services.analytics.aggregation import build_cross_module_profile
    from datetime import datetime, timedelta
    
    agent = ErrorDNAAgent()
    
    try:
        # Get DB session
        async for db in get_db():
            # Build error profile
            since = datetime.utcnow() - timedelta(days=request.period_days)
            profile = await build_cross_module_profile(request.user_id, db, since)
            
            # Run analysis
            result = await agent.analyse_from_aggregation(profile)
            
            return {
                "analysis": result.model_dump(),
                "profile_summary": {
                    "weakest_skill": profile.weakest_skill,
                    "strongest_skill": profile.strongest_skill,
                    "total_patterns": len(profile.top_error_patterns),
                    "period_start": profile.period_start.isoformat(),
                    "period_end": profile.period_end.isoformat(),
                }
            }
    except LLMClientError as e:
        logger.error("Error DNA analysis failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error DNA error")
        raise HTTPException(status_code=500, detail=f"Error DNA analysis failed: {str(e)}")


# ─────────────────────────────────────────────
#  Error DNA Micro-Exercises
# ─────────────────────────────────────────────

from services.agents.error_dna import MicroExerciseSet, MicroExerciseRequest, generate_micro_exercises

@router.post("/error-dna/micro-exercises", response_model=MicroExerciseSet)
async def error_dna_micro_exercises(request: MicroExerciseRequest):
    """
    Generate targeted micro-exercises for a specific error signature.
    
    Use this to generate practice drills that directly address an identified
    error pattern. Returns 3-5 exercises with explanations.
    
    The exercises are designed to help the student recognize and avoid
    the specific error pattern in future practice.
    """
    try:
        return await generate_micro_exercises(request)
    except LLMClientError as e:
        logger.error("Micro-exercise generation failed: %s", e)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected micro-exercise error")
        raise HTTPException(status_code=500, detail=f"Micro-exercise generation failed: {str(e)}")
