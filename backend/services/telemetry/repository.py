from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import TelemetrySession, TelemetrySummary, AttentionScore

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
