"""Writing Service — AI-generated tasks, essay submission, Gemma 4 rubric scoring."""
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
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
from services.agents.council import run_council


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

    if task_type == "task_1":
        return f"""You are an IELTS writing examiner. Generate a realistic IELTS TASK 1 Academic writing prompt{topic_clause}.

Requirements:
- The task MUST include chart/graph data that the student will describe.
- Choose one chart type: bar, line, or pie.
- Generate realistic numerical data with 4-8 data points.
- The task should be appropriate for a target Band {target_band} candidate.

Return a JSON object with exactly these fields:
{{
  "prompt": "The full question/prompt text shown to the student (e.g. 'The bar chart below shows...')",
  "description": "Brief instruction (e.g. 'Summarise the information by selecting and reporting the main features, and make comparisons where relevant.')",
  "band_descriptor": "Description of what a Band {target_band} answer looks like (2-3 sentences)",
  "chart_data": {{
    "chart_type": "bar | line | pie",
    "title": "Chart title shown above the visualization",
    "x_axis_label": "Label for the x-axis (not used for pie)",
    "y_axis_label": "Label for the y-axis (not used for pie)",
    "labels": ["Label1", "Label2", "..."],
    "datasets": [
      {{"label": "Series name", "data": [number, number, ...]}}
    ]
  }}
}}

IMPORTANT: chart_data.datasets[].data must contain only numbers. labels must match the number of data points.
Return ONLY valid JSON."""

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
        raw = await asyncio.to_thread(client.generate_text, prompt, None, 0.7)

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
                "chart_data": data.get("chart_data"),
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
            chart_data=data.get("chart_data"),
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
            chart_data=(t.generation_params or {}).get("chart_data"),
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
        chart_data=(task.generation_params or {}).get("chart_data"),
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

    # Score with Gemma 4 — use Council of Judges first, fall back to single-agent
    council_report = None
    try:
        council_report = await run_council(
            essay=request.essay,
            task_type=task.task_type,
            task_prompt=task.prompt,
            target_band=7.0,
        )
        # Map council verdict into WritingFeedback schema
        chief = council_report.chief
        feedback = WritingFeedback(
            task_response=chief.task_response,
            coherence=chief.coherence,
            lexical=chief.lexical,
            grammar=chief.grammar,
            overall=chief.overall_band,
            per_criterion_feedback=[
                {
                    "criterion": "task_response",
                    "band": chief.task_response,
                    "explanation": council_report.cohesion.explanation,
                    "improvement_tip": next(
                        (tip for tip in chief.priority_improvements if "task" in tip.lower() or "argument" in tip.lower()),
                        chief.priority_improvements[0] if chief.priority_improvements else "",
                    ),
                },
                {
                    "criterion": "coherence",
                    "band": chief.coherence,
                    "explanation": council_report.cohesion.explanation,
                    "improvement_tip": f"Cohesive devices found: {', '.join(council_report.cohesion.cohesive_devices_used[:3])}",
                },
                {
                    "criterion": "lexical",
                    "band": chief.lexical,
                    "explanation": council_report.lexical.explanation,
                    "improvement_tip": f"Upgrade these words: {', '.join(council_report.lexical.weak_vocabulary[:3])}",
                },
                {
                    "criterion": "grammar",
                    "band": chief.grammar,
                    "explanation": council_report.syntax.explanation,
                    "improvement_tip": council_report.syntax.grammar_errors[0] if council_report.syntax.grammar_errors else "Focus on using a wider range of complex structures.",
                },
            ],
            inline_corrections=[],
        )
    except Exception:
        # Council unavailable — fall back to single-agent scoring
        council_report = None
        try:
            client = get_gemma_client()
            prompt = _build_scoring_prompt(request.essay, task.task_type)
            feedback = await asyncio.to_thread(
                client.generate_structured,
                prompt=prompt,
                schema=WritingFeedback,
                temperature=0.3,
            )
        except GemmaClientError:
            feedback = _fallback_feedback()

    # Update session — store council report if available
    session.score = feedback.overall * 10
    session.band_estimate = feedback.overall
    feedback_data = feedback.model_dump()
    if council_report:
        feedback_data["council_report"] = council_report.model_dump()
    session.feedback_data = feedback_data
    session.finished_at = datetime.utcnow()
    await db.commit()

    return WritingSubmitResponse(
        session_id=session.id,
        word_count=word_count,
        band_estimate=feedback.overall,
        feedback=feedback,
        council_report=council_report.model_dump() if council_report else None,
    )


# ============ Sentence Evaluation (Band Booster Scaffold) ============


class SentenceEvalRequest(BaseModel):
    sentence: str
    original_sentence: str
    target_band: float = 7.0


class SentenceEvalResponse(BaseModel):
    estimated_band: float
    passes_threshold: bool
    structural_suggestions: str
    detected_grammar_features: list[str]


@router.post("/evaluate-sentence")
async def evaluate_sentence(request: SentenceEvalRequest):
    """
    Evaluate a single sentence for the Band Booster Scaffold.
    Returns an estimated band, pass/fail against target, and structural hints.
    Designed for fast 800ms debounced calls — uses a focused low-token prompt.
    """
    prompt = f"""You are an IELTS examiner evaluating a SINGLE sentence.
Evaluate ONLY grammar complexity and lexical range. Ignore content/topic.

TARGET BAND: {request.target_band}
SENTENCE: {request.sentence}

Rules:
- passes_threshold = true if estimated_band >= {request.target_band - 0.5}
- structural_suggestions: one short, specific upgrade hint (max 20 words)
- detected_grammar_features: list 1-3 grammar features present (e.g. "Simple S-V-O", "Relative clause")

Return JSON:
{{
  "estimated_band": <float 1.0-9.0>,
  "passes_threshold": <bool>,
  "structural_suggestions": "<hint>",
  "detected_grammar_features": ["<f1>", "<f2>"]
}}"""

    try:
        client = get_gemma_client()
        result = await asyncio.to_thread(
            client.generate_structured,
            prompt=prompt,
            schema=SentenceEvalResponse,
            temperature=0.1,
        )
        return result
    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentence evaluation failed: {str(e)}")
