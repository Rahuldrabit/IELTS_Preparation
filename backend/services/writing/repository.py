from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import WritingTask, Session as PracticeSession


async def create_writing_task(db: AsyncSession, task: WritingTask) -> WritingTask:
    db.add(task)
    await db.flush()
    return task


async def get_writing_tasks(db: AsyncSession, limit: int = 20, offset: int = 0) -> List[WritingTask]:
    query = select(WritingTask).order_by(WritingTask.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_writing_task(db: AsyncSession, task_id: int) -> Optional[WritingTask]:
    result = await db.execute(select(WritingTask).where(WritingTask.id == task_id))
    return result.scalar_one_or_none()


async def create_practice_session(db: AsyncSession, session: PracticeSession) -> PracticeSession:
    db.add(session)
    await db.flush()
    return session
