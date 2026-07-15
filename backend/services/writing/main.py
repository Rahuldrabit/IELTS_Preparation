"""Writing Service — AI-generated tasks, essay submission, Gemma 4 rubric scoring."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import WritingTask, Session as PracticeSession
from shared.schemas import (
    WritingFeedback,
    WritingTaskPublic,
    WritingSubmitRequest,
    WritingSubmitResponse,
    GenerateWritingTaskRequest,
)
from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError


# ============ Router ============

router = APIRouter(prefix="/writing", tags=["Writing"])


# ============ Prompt Builders ============


def _build_scoring_prompt(essay: str, task_type: str) -> str:
    """Build the Gemma 4 prompt for IELTS writing rubric scoring."""
    return f"""You are an expert IELTS examiner. Grade this Task {task_type.replace("_", " ").upper()} essay against the 4 official IELTS criteria.

CRITERIA:
1. Task Response (Task Achievement for Task 1) — How well did the candidate address all parts of the task?
2. Coherence and Cohesion — Is the response logically organised? Is there appropriate linking?
3. Lexical Resource — Range and accuracy of vocabulary.
4. Grammatical Range and Accuracy — Range of structures and error rate.

ESSAY:
{essay}

For EACH criterion provide:
- A band score (1.0–9.0) to one decimal place
- A 2–3 sentence explanation of why that score was awarded
- A specific improvement tip

Also list any specific inline corrections: find grammar, vocabulary, punctuation, or spelling mistakes.
For each correction provide the exact incorrect text, the corrected text, an explanation, and the error type.

Return JSON matching the WritingFeedback schema."""


def _build_task_generation_prompt(task_type: str, topic: Optional[str], target_band: float) -> str:
    """Build the Gemma 4 prompt for generating a fresh IELTS writing task."""
    topic_clause = f" on the topic of: {topic}" if topic else ""

    return f"""You are an IELTS writing examiner. Generate a realistic IELTS {task_type.replace('_', ' ').upper()} writing prompt{topic_clause}.

Requirements:
- The task should be appropriate for a target Band {target_band} candidate.
- Include a clear task description/instruction.
- Include a brief band descriptor showing what a good answer looks like.

Return a JSON object with exactly these fields:
{{
  "prompt": "The full question/prompt text shown to the student",
  "description": "Brief context or instruction (2-3 sentences)",
  "band_descriptor": "Description of what a Band {target_band} answer looks like (2-3 sentences)"
}}

Return ONLY valid JSON."""


def _fallback_feedback() -> WritingFeedback:
    """Return a safe fallback when Gemma 4 is unavailable."""
    return WritingFeedback(
        task_response=6.0,
        coherence=6.0,
        lexical=6.0,
        grammar=6.0,
        overall=6.0,
        per_criterion_feedback=[
            {
                "criterion": "task_response",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable. Please try again later.",
                "improvement_tip": "Try again after a few moments.",
            },
            {
                "criterion": "coherence",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable.",
                "improvement_tip": "Ensure your essay has a clear introduction, body, and conclusion.",
            },
            {
                "criterion": "lexical",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable.",
                "improvement_tip": "Use a range of academic vocabulary.",
            },
            {
                "criterion": "grammar",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable.",
                "improvement_tip": "Use a mix of simple and complex sentence structures.",
            },
        ],
        inline_corrections=[],
    )


# ============ Endpoints ============


@router.post("/generate-task")
async def generate_writing_task(
    request: GenerateWritingTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a fresh AI writing task prompt using Gemma 4."""
    try:
        client = get_gemma_client()
        prompt = _build_task_generation_prompt(
            task_type=request.task_type,
            topic=request.topic,
            target_band=request.target_band,
        )
        raw = client.generate_text(prompt, temperature=0.7)

        # Parse the JSON response
        import json
        if "{" in raw:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            data = json.loads(raw[start:end])
        else:
            raise ValueError("No JSON found in response")

        task = WritingTask(
            task_type=request.task_type,
            prompt=data.get("prompt", ""),
            description=data.get("description", ""),
            min_words=150 if request.task_type == "task_1" else 250,
            band_descriptor=data.get("band_descriptor", ""),
            generation_params={
                "topic": request.topic,
                "target_band": request.target_band,
            },
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return WritingTaskPublic(
            id=task.id,
            task_type=task.task_type,
            prompt=task.prompt,
            description=task.description,
            min_words=task.min_words,
            band_descriptor=task.band_descriptor,
        )

    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task generation failed: {str(e)}")


@router.get("/tasks")
async def get_tasks(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get all writing tasks."""
    query = (
        select(WritingTask)
        .order_by(WritingTask.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    tasks = result.scalars().all()

    return [
        WritingTaskPublic(
            id=t.id,
            task_type=t.task_type,
            prompt=t.prompt,
            description=t.description,
            min_words=t.min_words,
            band_descriptor=t.band_descriptor,
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific writing task."""
    result = await db.execute(
        select(WritingTask).where(WritingTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return WritingTaskPublic(
        id=task.id,
        task_type=task.task_type,
        prompt=task.prompt,
        description=task.description,
        min_words=task.min_words,
        band_descriptor=task.band_descriptor,
    )


@router.post("/submit")
async def submit_essay(
    request: WritingSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit an essay for Gemma 4 rubric scoring. Returns structured feedback."""
    # Validate task exists
    task_result = await db.execute(
        select(WritingTask).where(WritingTask.id == request.task_id)
    )
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    word_count = len(request.essay.split())

    # Create session
    session = PracticeSession(
        user_id=1,  # MVP: hardcoded user
        skill="writing",
        writing_task_id=request.task_id,
        user_content=request.essay,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Score with Gemma 4
    try:
        client = get_gemma_client()
        prompt = _build_scoring_prompt(request.essay, task.task_type)
        feedback: WritingFeedback = client.generate_structured(
            prompt=prompt,
            schema=WritingFeedback,
            temperature=0.3,
        )
    except GemmaClientError:
        feedback = _fallback_feedback()

    # Update session
    session.score = feedback.overall * 10
    session.band_estimate = feedback.overall
    session.feedback_data = feedback.model_dump()
    session.finished_at = datetime.utcnow()
    await db.commit()

    return WritingSubmitResponse(
        session_id=session.id,
        word_count=word_count,
        band_estimate=feedback.overall,
        feedback=feedback,
    )
