from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import User, Session, ErrorSignature, WeeklyErrorReport

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_latest_weekly_error_report(db: AsyncSession, user_id: int) -> Optional[WeeklyErrorReport]:
    result = await db.execute(
        select(WeeklyErrorReport)
        .where(WeeklyErrorReport.user_id == user_id)
        .order_by(WeeklyErrorReport.week_start.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

async def get_error_signatures(db: AsyncSession, user_id: int, status: str, limit: int) -> List[ErrorSignature]:
    result = await db.execute(
        select(ErrorSignature)
        .where(and_(
            ErrorSignature.user_id == user_id,
            ErrorSignature.status == status,
        ))
        .order_by(ErrorSignature.occurrences.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_error_signature_by_key(db: AsyncSession, user_id: int, pattern_key: str) -> Optional[ErrorSignature]:
    result = await db.execute(
        select(ErrorSignature).where(and_(
            ErrorSignature.user_id == user_id,
            ErrorSignature.pattern_key == pattern_key,
        ))
    )
    return result.scalar_one_or_none()

async def create_error_signature(db: AsyncSession, signature: ErrorSignature) -> ErrorSignature:
    db.add(signature)
    await db.flush()
    return signature

async def create_weekly_error_report(db: AsyncSession, report: WeeklyErrorReport) -> WeeklyErrorReport:
    db.add(report)
    await db.flush()
    return report

async def get_active_users_last_30_days(db: AsyncSession, thirty_days_ago: datetime) -> List[User]:
    result = await db.execute(
        select(User)
        .join(User.sessions)
        .where(Session.started_at >= thirty_days_ago)
        .distinct()
    )
    return result.scalars().all()
