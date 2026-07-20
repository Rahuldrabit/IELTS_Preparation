from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import ListeningSection, ListeningQuestion, Session as PracticeSession, UserResponse
from shared.schemas import ExamOutput
from .schemas import GenerateListeningRequest


async def create_listening_section(db: AsyncSession, section: ListeningSection) -> ListeningSection:
    db.add(section)
    await db.flush()
    return section


async def create_listening_question(db: AsyncSession, question: ListeningQuestion) -> ListeningQuestion:
    db.add(question)
    return question


async def create_practice_session(db: AsyncSession, session: PracticeSession) -> PracticeSession:
    db.add(session)
    await db.flush()
    return session


async def get_listening_tests(db: AsyncSession, limit: int = 20, offset: int = 0, difficulty: Optional[str] = None) -> List[ListeningSection]:
    query = select(ListeningSection).order_by(ListeningSection.created_at.desc())
    if difficulty:
        query = query.where(ListeningSection.difficulty == difficulty)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_listening_section(db: AsyncSession, test_id: int) -> Optional[ListeningSection]:
    result = await db.execute(
        select(ListeningSection).where(ListeningSection.id == test_id)
    )
    return result.scalar_one_or_none()


async def get_listening_questions_by_section(db: AsyncSession, section_id: int) -> List[ListeningQuestion]:
    result = await db.execute(
        select(ListeningQuestion).where(ListeningQuestion.section_id == section_id)
    )
    return result.scalars().all()


async def get_practice_session(db: AsyncSession, session_id: int, skill: str = "listening") -> Optional[PracticeSession]:
    result = await db.execute(
        select(PracticeSession).where(
            and_(PracticeSession.id == session_id, PracticeSession.skill == skill)
        )
    )
    return result.scalar_one_or_none()


async def create_user_response(db: AsyncSession, response: UserResponse) -> UserResponse:
    db.add(response)
    return response


async def get_user_dictation_responses(db: AsyncSession, user_id: int = 1) -> List[Tuple[UserResponse, PracticeSession]]:
    result = await db.execute(
        select(UserResponse, PracticeSession)
        .join(PracticeSession, UserResponse.session_id == PracticeSession.id)
        .where(and_(
            PracticeSession.user_id == user_id,
            UserResponse.error_type == "dictation_mishearing",
        ))
        .order_by(UserResponse.created_at.desc())
    )
    return result.all()
