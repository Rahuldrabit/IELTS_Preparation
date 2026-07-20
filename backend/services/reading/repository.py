from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import ReadingPassage, ReadingQuestion, Session as PracticeSession, UserResponse


async def create_reading_passage(db: AsyncSession, passage: ReadingPassage) -> ReadingPassage:
    db.add(passage)
    await db.flush()
    return passage


async def create_reading_question(db: AsyncSession, question: ReadingQuestion) -> ReadingQuestion:
    db.add(question)
    return question


async def create_practice_session(db: AsyncSession, session: PracticeSession) -> PracticeSession:
    db.add(session)
    await db.flush()
    return session


async def get_reading_passages(db: AsyncSession, limit: int = 20, offset: int = 0, difficulty: Optional[str] = None) -> List[ReadingPassage]:
    query = select(ReadingPassage).order_by(ReadingPassage.created_at.desc())
    if difficulty:
        query = query.where(ReadingPassage.difficulty == difficulty)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_reading_passage(db: AsyncSession, passage_id: int) -> Optional[ReadingPassage]:
    result = await db.execute(
        select(ReadingPassage).where(ReadingPassage.id == passage_id)
    )
    return result.scalar_one_or_none()


async def get_reading_questions_by_passage(db: AsyncSession, passage_id: int) -> List[ReadingQuestion]:
    result = await db.execute(
        select(ReadingQuestion).where(ReadingQuestion.passage_id == passage_id)
    )
    return result.scalars().all()


async def get_practice_session(db: AsyncSession, session_id: int, skill: str = "reading") -> Optional[PracticeSession]:
    result = await db.execute(
        select(PracticeSession).where(
            and_(PracticeSession.id == session_id, PracticeSession.skill == skill)
        )
    )
    return result.scalar_one_or_none()


async def create_user_response(db: AsyncSession, response: UserResponse) -> UserResponse:
    db.add(response)
    return response
