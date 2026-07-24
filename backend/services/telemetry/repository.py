from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import TelemetrySession, TelemetrySummary, AttentionScore, UserGazeCalibration

async def create_session(db: AsyncSession, session: TelemetrySession) -> TelemetrySession:
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def get_session(db: AsyncSession, session_id: int) -> Optional[TelemetrySession]:
    result = await db.execute(
        select(TelemetrySession).where(TelemetrySession.id == session_id)
    )
    return result.scalar_one_or_none()

async def create_summary(db: AsyncSession, summary: TelemetrySummary) -> TelemetrySummary:
    db.add(summary)
    await db.commit()
    return summary

async def end_session(db: AsyncSession, session_id: int) -> None:
    session = await get_session(db, session_id)
    if session:
        session.ended_at = datetime.utcnow()
        await db.commit()

async def get_summaries_by_session(db: AsyncSession, session_id: int) -> List[TelemetrySummary]:
    result = await db.execute(
        select(TelemetrySummary)
        .where(TelemetrySummary.telemetry_session_id == session_id)
        .order_by(TelemetrySummary.recorded_at)
    )
    return result.scalars().all()

async def get_latest_attention_score(db: AsyncSession, session_id: int) -> Optional[AttentionScore]:
    result = await db.execute(
        select(AttentionScore)
        .where(AttentionScore.telemetry_session_id == session_id)
        .order_by(AttentionScore.computed_at.desc())
    )
    return result.scalar_one_or_none()

async def get_sessions_by_user(db: AsyncSession, user_id: int) -> List[TelemetrySession]:
    result = await db.execute(
        select(TelemetrySession)
        .where(TelemetrySession.user_id == user_id)
        .order_by(TelemetrySession.started_at.desc())
    )
    return result.scalars().all()

async def get_summaries_for_sessions(db: AsyncSession, session_ids: List[int]) -> List[TelemetrySummary]:
    result = await db.execute(
        select(TelemetrySummary)
        .where(TelemetrySummary.telemetry_session_id.in_(session_ids))
    )
    return result.scalars().all()


async def get_user_calibration(
    db: AsyncSession, user_id: int, screen_width: int, screen_height: int
) -> Optional[UserGazeCalibration]:
    result = await db.execute(
        select(UserGazeCalibration)
        .where(UserGazeCalibration.user_id == user_id)
        .where(UserGazeCalibration.screen_width == screen_width)
        .where(UserGazeCalibration.screen_height == screen_height)
        .order_by(UserGazeCalibration.updated_at.desc())
    )
    return result.scalars().first()

async def save_user_calibration(
    db: AsyncSession, user_id: int, schema: "UserGazeCalibrationCreate"
) -> UserGazeCalibration:
    # Check if exists
    existing = await get_user_calibration(db, user_id, schema.screen_width, schema.screen_height)
    if existing:
        existing.calibration_matrix = schema.calibration_matrix
        existing.accuracy_score = schema.accuracy_score
        existing.device_pixel_ratio = schema.device_pixel_ratio
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing
        
    new_cal = UserGazeCalibration(
        user_id=user_id,
        screen_width=schema.screen_width,
        screen_height=schema.screen_height,
        device_pixel_ratio=schema.device_pixel_ratio,
        calibration_matrix=schema.calibration_matrix,
        accuracy_score=schema.accuracy_score,
    )
    db.add(new_cal)
    await db.commit()
    await db.refresh(new_cal)
    return new_cal

async def delete_user_calibration(db: AsyncSession, user_id: int) -> None:
    # Delete all calibrations for user
    result = await db.execute(
        select(UserGazeCalibration).where(UserGazeCalibration.user_id == user_id)
    )
    cals = result.scalars().all()
    for c in cals:
        await db.delete(c)
    await db.commit()
