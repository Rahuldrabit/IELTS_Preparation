from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import GrammarSkill, GrammarMistake, GrammarExercise, GrammarNote

async def get_skill_by_name(db: AsyncSession, user_id: int, skill_name: str) -> GrammarSkill:
    result = await db.execute(
        select(GrammarSkill)
        .where(GrammarSkill.user_id == user_id)
        .where(GrammarSkill.skill_name == skill_name)
    )
    return result.scalar_one_or_none()

async def get_recent_mistakes(db: AsyncSession, skill_id: int, limit: int = 5) -> list[GrammarMistake]:
    result = await db.execute(
        select(GrammarMistake)
        .where(GrammarMistake.skill_id == skill_id)
        .order_by(GrammarMistake.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_exercise_by_id(db: AsyncSession, exercise_id: int) -> GrammarExercise:
    result = await db.execute(
        select(GrammarExercise).where(GrammarExercise.id == exercise_id)
    )
    return result.scalar_one_or_none()

async def get_note_by_id(db: AsyncSession, user_id: int, note_id: int) -> GrammarNote:
    result = await db.execute(
        select(GrammarNote)
        .where(GrammarNote.id == note_id)
        .where(GrammarNote.user_id == user_id)
    )
    return result.scalar_one_or_none()
