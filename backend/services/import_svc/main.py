"""Import Service — VLM-powered exam import using Gemma 4.

Replaces Tesseract OCR with google-genai vision model (gemma-4-27b-it).
The model ingests an image and returns a fully structured ExamOutput JSON.
"""
import asyncio
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db, settings
from shared.models import ImportJob, ReadingPassage, ReadingQuestion, Session as PracticeSession
from shared.schemas import ExamOutput, GenerationParams, ImportStatusResponse
from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError


# ============ Router ============

router = APIRouter(prefix="/import", tags=["Import"])


# ============ VLM Import Functions ============


def _build_vlm_prompt() -> str:
    """Build the prompt for Gemma 4 VLM to extract exam content from image."""
    return """Analyze this IELTS exam page image carefully.

Your task:
1. Extract the reading passage text with paragraph IDs (A, B, C, D, etc.)
2. Identify all question groups and their types:
   - TRUE_FALSE_NOT_GIVEN
   - MATCHING_HEADINGS
   - SUMMARY_COMPLETION
   - MULTIPLE_CHOICE
   - SENTENCE_COMPLETION
   - FILL_BLANK
3. For each question, extract:
   - The question text
   - Options (if applicable)
   - The correct answer from the passage
   - The paragraph where the answer evidence is found (paragraph_anchor_id)
   - The evidence text (verbatim sentence(s))
   - Cognitive distractor analysis (why students might pick a wrong answer)

Requirements:
- Combine the passage into paragraphs labeled A, B, C, etc.
- Group questions by their section/type
- If you cannot determine a correct answer, make your best educated guess based on the passage
- Generate paragraph_anchor_id and evidence_text for every question

Return JSON matching the ExamOutput schema."""


def _store_exam_output(exam: ExamOutput, db_session) -> ReadingPassage:
    """Store VLM-generated exam in the database (same path as reading generate)."""
    content = "\n\n".join([p.text for p in exam.paragraphs])
    word_count = len(content.split())

    passage = ReadingPassage(
        title=exam.title,
        content=content,
        word_count=word_count,
        difficulty=exam.generation_params.difficulty if exam.generation_params else "medium",
        source="vlm_import",
        generation_params=exam.generation_params.model_dump() if exam.generation_params else None,
    )
    db_session.add(passage)
    db_session.flush()

    for group in exam.question_groups:
        for q in group.questions:
            question = ReadingQuestion(
                passage_id=passage.id,
                question_text=q.prompt_text,
                question_type=group.question_type,
                group_id=group.group_id,
                question_number=q.question_number,
                options=q.local_options,
                correct_answer=q.backend_evaluation.correct_answer,
                explanation=q.backend_evaluation.evidence_text,
                question_evaluation=q.backend_evaluation.model_dump(),
            )
            db_session.add(question)

    db_session.commit()
    db_session.refresh(passage)
    return passage


async def process_import_job_vlm(import_id: int, file_paths: list[str], db_url: str):
    """Background task to process import using Gemma 4 VLM."""
    from shared.database import async_session_maker
    from sqlalchemy import text

    async with async_session_maker() as db:
        try:
            # Update job status
            job_result = await db.execute(
                select(ImportJob).where(ImportJob.id == import_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                job.status = "processing"
                await db.commit()

            # Process each image through VLM
            client = get_gemma_client()
            prompt = _build_vlm_prompt()

            for path in file_paths:
                if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                    continue

                try:
                    exam: ExamOutput = client.generate_structured(
                        prompt=prompt,
                        schema=ExamOutput,
                        image_path=path,
                        temperature=0.0,
                    )

                    # Store in DB
                    passage = _store_exam_output(exam, db)

                    # Create a session for the imported content
                    session = PracticeSession(
                        user_id=1,
                        skill="reading",
                        passage_id=passage.id,
                        started_at=datetime.utcnow(),
                    )
                    db.add(session)
                    await db.commit()

                    # Update job with passage_id
                    if job:
                        job.status = "completed"
                        job.passage_id = passage.id
                        await db.commit()

                except GemmaClientError as e:
                    if job:
                        job.status = "failed"
                        job.error_message = f"VLM processing failed: {str(e)}"
                        await db.commit()
                    return

        except Exception as e:
            job_result = await db.execute(
                select(ImportJob).where(ImportJob.id == import_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                await db.commit()


# ============ Endpoints ============


@router.post("/reading")
async def import_reading(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Import reading material via Gemma 4 VLM vision model."""
    import_id = uuid.uuid4().int % 1000000

    import_dir = settings.import_storage_path
    os.makedirs(import_dir, exist_ok=True)

    file_paths = []
    for file in files:
        file_path = os.path.join(import_dir, f"{import_id}_{file.filename}")
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        file_paths.append(file_path)

    job = ImportJob(
        id=import_id,
        import_type="reading",
        status="pending",
        file_paths=file_paths,
    )
    db.add(job)
    await db.commit()

    # Launch VLM processing in background
    background_tasks.add_task(
        process_import_job_vlm,
        import_id,
        file_paths,
        settings.database_url_sync,
    )

    return {"import_id": import_id, "status": "pending"}


@router.get("/{import_id}/status")
async def get_import_status(import_id: int, db: AsyncSession = Depends(get_db)):
    """Get status of import job. Returns session_id when completed."""
    result = await db.execute(select(ImportJob).where(ImportJob.id == import_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    # If completed, look up the session
    session_id = None
    if job.passage_id and job.status == "completed":
        session_result = await db.execute(
            select(PracticeSession).where(
                PracticeSession.passage_id == job.passage_id
            )
        )
        session = session_result.scalar_one_or_none()
        if session:
            session_id = session.id

    # Check if no questions were found
    needs_questions = False
    if job.passage_id:
        q_result = await db.execute(
            select(ReadingQuestion).where(ReadingQuestion.passage_id == job.passage_id)
        )
        questions = q_result.scalars().all()
        if len(questions) == 0:
            needs_questions = True

    return ImportStatusResponse(
        import_id=import_id,
        status=job.status,
        passage_id=job.passage_id,
        session_id=session_id,
        needs_question_generation=needs_questions,
        error=job.error_message,
    )


@router.post("/listening")
async def import_listening(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    questions: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
):
    """Import listening material (audio + question images) via Gemma 4 VLM.

    The audio is stored; question images are processed through VLM to extract
    a structured ExamOutput. This reuses the same VLM pipeline as reading import.
    """
    import_id = uuid.uuid4().int % 1000000

    import_dir = settings.import_storage_path
    os.makedirs(import_dir, exist_ok=True)

    # Save audio
    audio_path = os.path.join(import_dir, f"{import_id}_audio_{audio.filename}")
    audio_content = await audio.read()
    with open(audio_path, "wb") as f:
        f.write(audio_content)

    # Save question images
    file_paths = [audio_path]
    for file in questions:
        file_path = os.path.join(import_dir, f"{import_id}_{file.filename}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        file_paths.append(file_path)

    job = ImportJob(
        id=import_id,
        import_type="listening",
        status="pending",
        file_paths=file_paths,
    )
    db.add(job)
    await db.commit()

    # Process question images through VLM (same as reading)
    background_tasks.add_task(
        process_import_job_vlm,
        import_id,
        file_paths,
        settings.database_url_sync,
    )

    return {"import_id": import_id, "status": "pending"}
