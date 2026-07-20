from typing import Optional, List
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import MockTest, MockTestSection, User

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_mock_test(db: AsyncSession, mock_test_id: int, user_id: int) -> Optional[MockTest]:
    result = await db.execute(select(MockTest).where(and_(MockTest.id == mock_test_id, MockTest.user_id == user_id)))
    return result.scalar_one_or_none()

async def get_in_progress_mock_test(db: AsyncSession, user_id: int) -> Optional[MockTest]:
    result = await db.execute(select(MockTest).where(and_(MockTest.user_id == user_id, MockTest.status == "in_progress")))
    return result.scalar_one_or_none()

async def get_latest_completed_mock_test(db: AsyncSession, user_id: int) -> Optional[MockTest]:
    result = await db.execute(select(MockTest).where(MockTest.user_id == user_id).order_by(desc(MockTest.created_at)).limit(1))
    return result.scalar_one_or_none()

async def get_completed_baseline_test(db: AsyncSession, user_id: int) -> Optional[MockTest]:
    result = await db.execute(select(MockTest).where(and_(MockTest.user_id == user_id, MockTest.test_type == "baseline", MockTest.status == "completed")))
    return result.scalar_one_or_none()

async def get_mock_test_history(db: AsyncSession, user_id: int, limit: int, offset: int) -> List[MockTest]:
    result = await db.execute(select(MockTest).where(MockTest.user_id == user_id).order_by(desc(MockTest.created_at)).offset(offset).limit(limit))
    return result.scalars().all()

async def get_mock_test_section(db: AsyncSession, mock_test_id: int, section_type: str) -> Optional[MockTestSection]:
    result = await db.execute(select(MockTestSection).where(and_(MockTestSection.mock_test_id == mock_test_id, MockTestSection.section_type == section_type)))
    return result.scalar_one_or_none()

async def create_mock_test(db: AsyncSession, mock_test: MockTest) -> MockTest:
    db.add(mock_test)
    await db.flush()
    return mock_test

async def create_mock_test_section(db: AsyncSession, section: MockTestSection) -> MockTestSection:
    db.add(section)
    return section
