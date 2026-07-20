from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from . import schemas
from services.agents.mentor import MentorAgent
from services.llm import LLMClientError

router = APIRouter(prefix="/agent", tags=["Chat & Mentor"])

@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest):
    agent = MentorAgent()
    try:
        result = await agent.chat(
            message=request.message,
            page=request.page,
            context=request.context,
        )
        return schemas.ChatResponse(response=result.response, type=result.type)
    except LLMClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/mentor-messages", response_model=List[Dict[str, Any]])
async def get_mentor_messages(page: str = "dashboard"):
    agent = MentorAgent()
    try:
        msg = await agent.get_mentor_message(page=page)
        return [{"id": f"msg-{page}-1", "type": "greeting", "content": msg}]
    except LLMClientError:
        return [{"id": f"msg-{page}-1", "type": "greeting", "content": "You're doing great! Keep up the good work."}]
    except Exception:
        return [{"id": f"msg-{page}-1", "type": "greeting", "content": "Keep practicing every day to see improvement."}]


@router.get("/daily-plan", response_model=schemas.DailyPlan)
async def get_daily_plan():
    agent = MentorAgent()
    try:
        plan = await agent.generate_daily_plan()
        return plan
    except Exception:
        return schemas.DailyPlan(
            tasks=[
                schemas.DailyTask(title="Complete 2 reading passages", skill="reading", priority="high"),
                schemas.DailyTask(title="Practice 10 vocabulary words", skill="vocabulary", priority="medium"),
                schemas.DailyTask(title="Listen to a podcast and take notes", skill="listening", priority="medium"),
                schemas.DailyTask(title="Record a 2-minute speaking response", skill="speaking", priority="low"),
                schemas.DailyTask(title="Write an essay and get AI feedback", skill="writing", priority="high"),
            ]
        )

class CapabilitiesResponse(schemas.BaseModel):
    provider: str
    transcription: bool
    vision: bool
    structured_output: bool
    status: str

@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    try:
        from services.llm.provider import get_llm_client
        client = get_llm_client()
        provider = client.provider_name
        
        transcription_available = provider == "google"
        vision_available = provider == "google"
        
        return CapabilitiesResponse(
            provider=provider,
            transcription=transcription_available,
            vision=vision_available,
            structured_output=True,
            status="ok",
        )
    except Exception as e:
        return CapabilitiesResponse(
            provider="none",
            transcription=False,
            vision=False,
            structured_output=False,
            status=f"error: {str(e)}",
        )

@router.get("/health")
async def health_check():
    try:
        from services.llm.provider import get_llm_client
        client = get_llm_client()
        result = client.health_check()
        return result
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
