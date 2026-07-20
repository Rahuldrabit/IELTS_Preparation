import os
import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db, settings
from shared.schemas import ImportStatusResponse
from . import repository
from . import service

router = APIRouter(prefix="/import", tags=["Import"])

@router.post("/reading")
async def import_reading(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
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

    await repository.create_import_job(db, import_id, "reading", file_paths)

    background_tasks.add_task(
        service.process_import_job_vlm,
        import_id,
        file_paths,
        settings.database_url_sync,
        user_id,
    )

    return {"import_id": import_id, "status": "pending"}

@router.get("/{import_id}/status")
async def get_import_status(
    import_id: int, 
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db)
):
    job = await repository.get_import_job(db, import_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    session_id = None
    if job.passage_id and job.status == "completed":
        session = await repository.get_session_by_passage_id(db, job.passage_id)
        if session:
            session_id = session.id

    needs_questions = False
    if job.passage_id:
        count = await repository.count_questions_for_passage(db, job.passage_id)
        if count == 0:
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
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    import_id = uuid.uuid4().int % 1000000

    import_dir = settings.import_storage_path
    os.makedirs(import_dir, exist_ok=True)

    audio_path = os.path.join(import_dir, f"{import_id}_audio_{audio.filename}")
    audio_content = await audio.read()
    with open(audio_path, "wb") as f:
        f.write(audio_content)

    file_paths = [audio_path]
    for file in questions:
        file_path = os.path.join(import_dir, f"{import_id}_{file.filename}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        file_paths.append(file_path)

    await repository.create_import_job(db, import_id, "listening", file_paths)

    background_tasks.add_task(
        service.process_import_job_vlm,
        import_id,
        file_paths,
        settings.database_url_sync,
        user_id,
    )

    return {"import_id": import_id, "status": "pending"}
