from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import ImportJob, ReadingPassage, ReadingQuestion, Session as PracticeSession
from shared.schemas import ExamOutput

async def create_import_job(db: AsyncSession, import_id: int, import_type: str, file_paths: list[str]) -> ImportJob:
    job = ImportJob(
        id=import_id,
        import_type=import_type,
        status="pending",
        file_paths=file_paths,
    )
    db.add(job)
    await db.commit()
    return job

async def get_import_job(db: AsyncSession, import_id: int) -> ImportJob:
    result = await db.execute(select(ImportJob).where(ImportJob.id == import_id))
    return result.scalar_one_or_none()

async def update_job_status(db: AsyncSession, import_id: int, status: str, error_message: str = None, passage_id: int = None):
    job = await get_import_job(db, import_id)
    if job:
        job.status = status
        if error_message:
            job.error_message = error_message
        if passage_id:
            job.passage_id = passage_id
        await db.commit()

async def store_exam_output(db: AsyncSession, exam: ExamOutput, user_id: int = 1) -> ReadingPassage:
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
    db.add(passage)
    await db.flush()

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
            db.add(question)

    session = PracticeSession(
        user_id=user_id,
        skill="reading",
        passage_id=passage.id,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(passage)
    return passage

async def get_session_by_passage_id(db: AsyncSession, passage_id: int) -> PracticeSession:
    result = await db.execute(select(PracticeSession).where(PracticeSession.passage_id == passage_id))
    return result.scalar_one_or_none()

async def count_questions_for_passage(db: AsyncSession, passage_id: int) -> int:
    result = await db.execute(select(ReadingQuestion).where(ReadingQuestion.passage_id == passage_id))
    questions = result.scalars().all()
    return len(questions)
