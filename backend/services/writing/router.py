import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import Session as PracticeSession, WritingTask
from shared.schemas import (
    GenerateWritingTaskRequest,
    WritingSubmitRequest,
    WritingSubmitResponse,
    WritingFeedback,
)
from services.llm import LLMClientError
from services.agents.council import run_council
from services.agents.writing import WritingAgent
from shared.parsing import parse_json_from_response

from . import schemas
from . import repository
from . import service

router = APIRouter(prefix="/writing", tags=["Writing"])


@router.post("/generate-task")
async def generate_writing_task(
    request: GenerateWritingTaskRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    try:
        agent = WritingAgent()
        prompt = service.build_task_generation_prompt(
            task_type=request.task_type,
            topic=request.topic,
            target_band=request.target_band,
            )
        raw = await agent.run_text(prompt=prompt, temperature=0.7)

        data = parse_json_from_response(raw)
        if not data:
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
        task = await repository.create_writing_task(db, task)
        return service.build_writing_task_response(task, data.get("chart_data"))

    except LLMClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task generation failed: {str(e)}")


@router.get("/tasks")
async def get_tasks(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    tasks = await repository.get_writing_tasks(db, limit, offset)
    return [service.build_writing_task_response(t) for t in tasks]


@router.get("/tasks/{task_id}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await repository.get_writing_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return service.build_writing_task_response(task)


@router.post("/submit")
async def submit_essay(
    request: WritingSubmitRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    task = await repository.get_writing_task(db, request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    word_count = len(request.essay.split())

    session = PracticeSession(
        user_id=user_id,
        skill="writing",
        writing_task_id=request.task_id,
        user_content=request.essay,
        started_at=datetime.utcnow(),
    )
    session = await repository.create_practice_session(db, session)

    council_report = None
    try:
        council_report = await run_council(
            essay=request.essay,
            task_type=task.task_type,
            task_prompt=task.prompt,
            target_band=7.0,
        )
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
        feedback = service.fallback_feedback()

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


@router.post("/evaluate-sentence")
async def evaluate_sentence(request: schemas.SentenceEvalRequest):
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
        agent = WritingAgent()
        result = await agent.run_structured(
            prompt=prompt,
            schema=schemas.SentenceEvalResponse,
            temperature=0.1,
        )
        return result
    except LLMClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentence evaluation failed: {str(e)}")


@router.post("/handwritten/upload")
async def upload_handwritten_essay(
    file: UploadFile = File(...),
    task_type: str = Form("task_2"),
    topic: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    from services.writing.handwritten import (
        validate_image_file,
        save_temp_image,
        score_handwritten_essay,
        cleanup_temp_file,
    )
    
    extension = validate_image_file(file)
    temp_path = await save_temp_image(file, extension)
    
    try:
        result = await score_handwritten_essay(
            image_path=temp_path,
            task_type=task_type,
            topic=topic,
        )
        return result.model_dump()
    finally:
        cleanup_temp_file(temp_path)


@router.post("/handwritten/extract")
async def extract_handwritten_text(
    file: UploadFile = File(...),
):
    from services.writing.handwritten import (
        validate_image_file,
        save_temp_image,
        extract_text_from_image,
        cleanup_temp_file,
    )
    
    extension = validate_image_file(file)
    temp_path = await save_temp_image(file, extension)
    
    try:
        result = await extract_text_from_image(temp_path)
        return result.model_dump()
    finally:
        cleanup_temp_file(temp_path)
