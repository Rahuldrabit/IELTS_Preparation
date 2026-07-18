"""
Cognitive Telemetry Engine — Backend Service

Endpoints:
  POST /telemetry/session/start   → Create telemetry session
  POST /telemetry/upload          → Receive batched telemetry summaries
  POST /telemetry/event           → Single event ingestion (critical events)
  GET  /telemetry/report/{id}     → Get session analysis report
  GET  /telemetry/profile/{uid}   → Get user behavioral profile
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func
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
    AttentionScoreData,
)
from .models import TelemetrySession, TelemetrySummary, AttentionScore, QuestionBehavior

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


# ─────────────────────────────────────────────
#  POST /telemetry/session/start
# ─────────────────────────────────────────────

@router.post("/session/start", response_model=TelemetrySessionResponse)
async def start_session(
    body: TelemetrySessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new telemetry session for a reading/listening practice."""
    session = TelemetrySession(
        user_id=body.user_id,
        backend_session_id=body.backend_session_id,
        skill=body.skill,
        calibration_accuracy=body.calibration_accuracy,
        gaze_enabled=body.gaze_enabled,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return TelemetrySessionResponse(
        id=session.id,
        user_id=session.user_id,
        skill=session.skill,
        started_at=session.started_at,
    )


# ─────────────────────────────────────────────
#  POST /telemetry/upload
# ─────────────────────────────────────────────

@router.post("/upload", response_model=TelemetryUploadResponse)
async def upload_telemetry(
    body: TelemetryUploadRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive a batch of telemetry data (summary + events).
    Frontend sends this every 2 seconds during active sessions.
    """
    # Validate session exists
    result = await db.execute(
        select(TelemetrySession).where(TelemetrySession.id == body.telemetry_session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Telemetry session not found")

    # Store summary
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
        db.add(summary)

    # Store events count (we don't store raw events in DB, just metadata)
    # The summary is the aggregated representation.
    # Raw events are only stored if we need replay (future feature).

    await db.commit()

    return TelemetryUploadResponse(
        status="ok",
        events_received=body.event_count,
    )


# ─────────────────────────────────────────────
#  POST /telemetry/event
# ─────────────────────────────────────────────

@router.post("/event")
async def record_event(
    body: TelemetryEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """Record a single critical telemetry event (e.g., session_end)."""
    # For now, critical events update the session record
    if body.event_type == "session_end":
        result = await db.execute(
            select(TelemetrySession).where(TelemetrySession.id == body.telemetry_session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.ended_at = datetime.utcnow()
            await db.commit()

    return {"status": "ok"}


# ─────────────────────────────────────────────
#  GET /telemetry/report/{session_id}
# ─────────────────────────────────────────────

@router.get("/report/{session_id}", response_model=TelemetryReportResponse)
async def get_report(session_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get aggregated telemetry report for a completed session.
    Combines all summaries into a final analysis.
    """
    # Get session
    result = await db.execute(
        select(TelemetrySession).where(TelemetrySession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Aggregate all summaries for this session
    summaries_result = await db.execute(
        select(TelemetrySummary)
        .where(TelemetrySummary.telemetry_session_id == session_id)
        .order_by(TelemetrySummary.recorded_at)
    )
    summaries = summaries_result.scalars().all()

    if not summaries:
        raise HTTPException(status_code=404, detail="No telemetry data for this session")

    # Aggregate metrics
    total_fixations = sum(s.fixation_count for s in summaries)
    total_regressions = sum(s.regression_count for s in summaries)
    avg_focus = sum(s.focus_score for s in summaries) / len(summaries) if summaries else 0
    avg_fixation_ms = sum(s.avg_fixation_ms for s in summaries) / len(summaries) if summaries else 0
    avg_speed = sum(s.reading_speed_wpm for s in summaries) / len(summaries) if summaries else 0
    avg_blink = sum(s.blink_rate for s in summaries) / len(summaries) if summaries else 0
    avg_skip = sum(s.skip_rate for s in summaries) / len(summaries) if summaries else 0

    # Merge paragraph times
    merged_para_time: dict = {}
    for s in summaries:
        if s.paragraph_time:
            for para_id, time_ms in s.paragraph_time.items():
                merged_para_time[para_id] = merged_para_time.get(para_id, 0) + time_ms

    # Get attention score if computed
    attention_result = await db.execute(
        select(AttentionScore)
        .where(AttentionScore.telemetry_session_id == session_id)
        .order_by(AttentionScore.computed_at.desc())
    )
    attention = attention_result.scalar_one_or_none()

    return TelemetryReportResponse(
        session_id=session_id,
        skill=session.skill,
        duration_ms=int((session.ended_at - session.started_at).total_seconds() * 1000) if session.ended_at else None,
        total_fixations=total_fixations,
        total_regressions=total_regressions,
        avg_focus_score=round(avg_focus, 1),
        avg_fixation_ms=round(avg_fixation_ms, 1),
        avg_reading_speed_wpm=round(avg_speed, 1),
        avg_blink_rate=round(avg_blink, 1),
        avg_skip_rate=round(avg_skip, 3),
        paragraph_time=merged_para_time,
        attention_score=AttentionScoreData(
            overall=attention.overall_attention,
            scanning_efficiency=attention.scanning_efficiency,
            regression_severity=attention.regression_severity,
            time_management=attention.time_management,
            focus_stability=attention.focus_stability,
        ) if attention else None,
    )


# ─────────────────────────────────────────────
#  GET /telemetry/profile/{user_id}
# ─────────────────────────────────────────────

@router.get("/profile/{user_id}", response_model=TelemetryProfileResponse)
async def get_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get user's behavioral profile across all telemetry sessions.
    Useful for AI coaching prompts.
    """
    # Get all sessions for this user
    sessions_result = await db.execute(
        select(TelemetrySession)
        .where(TelemetrySession.user_id == user_id)
        .order_by(TelemetrySession.started_at.desc())
    )
    sessions = sessions_result.scalars().all()

    if not sessions:
        return TelemetryProfileResponse(
            user_id=user_id,
            total_sessions=0,
            avg_focus_score=0,
            avg_reading_speed_wpm=0,
            avg_regression_rate=0,
            strengths=[],
            weaknesses=[],
        )

    # Get latest summaries across all sessions
    session_ids = [s.id for s in sessions]
    summaries_result = await db.execute(
        select(TelemetrySummary)
        .where(TelemetrySummary.telemetry_session_id.in_(session_ids))
    )
    all_summaries = summaries_result.scalars().all()

    if not all_summaries:
        return TelemetryProfileResponse(
            user_id=user_id,
            total_sessions=len(sessions),
            avg_focus_score=0,
            avg_reading_speed_wpm=0,
            avg_regression_rate=0,
            strengths=[],
            weaknesses=[],
        )

    # Compute cross-session averages
    avg_focus = sum(s.focus_score for s in all_summaries) / len(all_summaries)
    avg_speed = sum(s.reading_speed_wpm for s in all_summaries) / len(all_summaries)
    total_fix = sum(s.fixation_count for s in all_summaries)
    total_reg = sum(s.regression_count for s in all_summaries)
    reg_rate = total_reg / total_fix if total_fix > 0 else 0

    # Simple heuristic for strengths/weaknesses
    strengths = []
    weaknesses = []

    if avg_focus >= 75:
        strengths.append("Sustained attention")
    elif avg_focus < 50:
        weaknesses.append("Focus drops during reading")

    if avg_speed >= 200:
        strengths.append("Fast reading speed")
    elif avg_speed < 120:
        weaknesses.append("Slow reading speed")

    if reg_rate < 0.1:
        strengths.append("Low regression rate")
    elif reg_rate > 0.25:
        weaknesses.append("High regression rate (comprehension difficulty)")

    return TelemetryProfileResponse(
        user_id=user_id,
        total_sessions=len(sessions),
        avg_focus_score=round(avg_focus, 1),
        avg_reading_speed_wpm=round(avg_speed, 1),
        avg_regression_rate=round(reg_rate, 3),
        strengths=strengths,
        weaknesses=weaknesses,
    )
