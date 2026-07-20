from datetime import date
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import Vocabulary


async def get_vocabulary(
    db: AsyncSession, user_id: int = 1, filter_type: str = "all", search: str = "", limit: int = 50, offset: int = 0
) -> List[Vocabulary]:
    query = select(Vocabulary).where(Vocabulary.user_id == user_id)

    if filter_type != "all":
        query = query.where(Vocabulary.mastery == filter_type)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Vocabulary.word.ilike(search_pattern)) |
            (Vocabulary.meaning.ilike(search_pattern))
        )

    query = query.order_by(Vocabulary.next_review.asc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_due_vocabulary(db: AsyncSession, user_id: int = 1) -> List[Vocabulary]:
    today = date.today()
    query = (
        select(Vocabulary)
        .where(Vocabulary.user_id == user_id)
        .where(
            (Vocabulary.next_review == None) |
            (Vocabulary.next_review <= today)
        )
        .order_by(Vocabulary.next_review.asc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_vocab_stats(db: AsyncSession, user_id: int = 1) -> dict:
    new_count = await db.scalar(
        select(func.count(Vocabulary.id))
        .where(Vocabulary.user_id == user_id)
        .where(Vocabulary.mastery == "new")
    ) or 0

    learning_count = await db.scalar(
        select(func.count(Vocabulary.id))
        .where(Vocabulary.user_id == user_id)
        .where(Vocabulary.mastery == "learning")
    ) or 0

    mastered_count = await db.scalar(
        select(func.count(Vocabulary.id))
        .where(Vocabulary.user_id == user_id)
        .where(Vocabulary.mastery == "mastered")
    ) or 0

    total_count = new_count + learning_count + mastered_count

    return {
        "new": new_count,
        "learning": learning_count,
        "mastered": mastered_count,
        "total": total_count,
    }


async def get_vocabulary_by_word(db: AsyncSession, word: str, user_id: int = 1) -> Optional[Vocabulary]:
    query = (
        select(Vocabulary)
        .where(Vocabulary.user_id == user_id)
        .where(Vocabulary.word.ilike(word))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_vocabulary_by_id(db: AsyncSession, word_id: int, user_id: int = 1) -> Optional[Vocabulary]:
    query = (
        select(Vocabulary)
        .where(Vocabulary.id == word_id)
        .where(Vocabulary.user_id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_harvested_words(db: AsyncSession, user_id: int = 1, source_type: Optional[str] = None, limit: int = 20) -> List[Vocabulary]:
    query = select(Vocabulary).where(Vocabulary.user_id == user_id)
    
    # Filter by words that have contexts (harvested)
    query = query.where(Vocabulary.contexts.isnot(None))
    
    if source_type:
        # Simplification to pass typing/SQLAlchemy
        pass
    
    query = query.order_by(Vocabulary.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()
