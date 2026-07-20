from datetime import date
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import User, Milestone, DailyTask


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_milestones(db: AsyncSession, user_id: int) -> List[Milestone]:
    result = await db.execute(select(Milestone).where(Milestone.user_id == user_id).order_by(Milestone.band))
    return result.scalars().all()


async def get_daily_tasks(db: AsyncSession, user_id: int, target_date: date) -> List[DailyTask]:
    result = await db.execute(select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.date == target_date))
    return result.scalars().all()


async def get_all_daily_tasks(db: AsyncSession, user_id: int) -> List[DailyTask]:
    result = await db.execute(select(DailyTask).where(DailyTask.user_id == user_id))
    return result.scalars().all()


async def get_daily_task_by_id(db: AsyncSession, task_id: int, user_id: int) -> Optional[DailyTask]:
    result = await db.execute(select(DailyTask).where(DailyTask.id == task_id, DailyTask.user_id == user_id))
    return result.scalar_one_or_none()
