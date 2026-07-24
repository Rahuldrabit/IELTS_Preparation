from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from .schemas import (
    TelemetrySessionCreate,
    TelemetrySessionResponse,
    TelemetryUploadRequest,
    TelemetryUploadResponse,
    TelemetryEventCreate,
    TelemetryReportResponse,
    TelemetryProfileResponse,
    UserGazeCalibrationCreate,
    UserGazeCalibrationResponse,
)
from fastapi.responses import FileResponse
from pathlib import Path

from .models import TelemetrySession, TelemetrySummary
from . import repository
from . import service

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

@router.post("/session/start", response_model=TelemetrySessionResponse)
async def start_session(
    body: TelemetrySessionCreate,
    user_id: int = 1, # Kept for consistency, even if body has user_id
    db: AsyncSession = Depends(get_db),
):
    session = TelemetrySession(
        user_id=body.user_id if body.user_id else user_id,
        backend_session_id=body.backend_session_id,
        skill=body.skill,
        calibration_accuracy=body.calibration_accuracy,
        gaze_enabled=body.gaze_enabled,
        started_at=datetime.utcnow(),
    )
    session = await repository.create_session(db, session)
    return TelemetrySessionResponse(
        id=session.id,
        user_id=session.user_id,
        skill=session.skill,
        started_at=session.started_at,
    )

@router.post("/upload", response_model=TelemetryUploadResponse)
async def upload_telemetry(
    body: TelemetryUploadRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await repository.get_session(db, body.telemetry_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Telemetry session not found")

    if body.summary:
        summary = TelemetrySummary(
            telemetry_session_id=body.telemetry_session_id,
            paragraph_time=body.summary.paragraph_time,
            fixation_count=body.summary.fixation_count,
            regression_count=body.summary.regression_count,
            skip_rate=body.summary.skip_rate,
            blink_rate=body.summary.blink_rate,
            focus_score=body.summary.focus_score,
            avg_fixation_ms=body.summary.avg_fixation_ms,
            reading_speed_wpm=body.summary.reading_speed_wpm,
            recorded_at=datetime.utcnow(),
        )
        await repository.create_summary(db, summary)

    return TelemetryUploadResponse(
        status="ok",
        events_received=body.event_count,
    )

@router.post("/event")
async def record_event(
    body: TelemetryEventCreate,
    db: AsyncSession = Depends(get_db),
):
    if body.event_type == "session_end":
        await repository.end_session(db, body.telemetry_session_id)
    return {"status": "ok"}

@router.get("/report/{session_id}", response_model=TelemetryReportResponse)
async def get_report(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await repository.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    summaries = await repository.get_summaries_by_session(db, session_id)
    if not summaries:
        raise HTTPException(status_code=404, detail="No telemetry data for this session")

    attention = await repository.get_latest_attention_score(db, session_id)
    
    return service.build_report_response(session, summaries, attention)

@router.get("/profile/{user_id}", response_model=TelemetryProfileResponse)
async def get_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    sessions = await repository.get_sessions_by_user(db, user_id)
    if not sessions:
        return service.build_profile_response(user_id, 0, [])

    session_ids = [s.id for s in sessions]
    all_summaries = await repository.get_summaries_for_sessions(db, session_ids)
    
    return service.build_profile_response(user_id, len(sessions), all_summaries)

@router.get("/calibration", response_model=UserGazeCalibrationResponse)
async def get_calibration(
    screen_width: int,
    screen_height: int,
    user_id: int = 1, # Default placeholder if auth is disabled
    db: AsyncSession = Depends(get_db),
):
    cal = await repository.get_user_calibration(db, user_id, screen_width, screen_height)
    if not cal:
        raise HTTPException(status_code=404, detail="Calibration not found for this screen resolution")
    return cal

@router.post("/calibration", response_model=UserGazeCalibrationResponse)
async def save_calibration(
    body: UserGazeCalibrationCreate,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    cal = await repository.save_user_calibration(db, user_id, body)
    return cal

@router.delete("/calibration")
async def delete_calibration(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    await repository.delete_user_calibration(db, user_id)
    return {"status": "deleted"}

@router.get("/models/{file_path:path}")
async def serve_model_files(file_path: str):
    # Base directory for the backend (assumes router is in services/telemetry)
    base_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "telemetry" / "models"
    file = base_dir / file_path
    
    # Prevent directory traversal
    try:
        file.resolve().relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid path")
        
    if not file.exists() or not file.is_file():
        raise HTTPException(status_code=404, detail="Model file not found")
        
    # Use appropriate media type for wasm
    media_type = "application/wasm" if file.suffix == ".wasm" else None
    
    return FileResponse(
        path=file,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )

