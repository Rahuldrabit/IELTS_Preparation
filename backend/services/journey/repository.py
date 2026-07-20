from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import User, Session, ErrorSignature

async def get_user(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_weak_skills(user_id: int, db: AsyncSession) -> dict[str, float]:
    result = await db.execute(
        select(ErrorSignature)
        .where(ErrorSignature.user_id == user_id)
        .where(ErrorSignature.status == "active")
        .order_by(ErrorSignature.severity.desc())
        .limit(20)
    )
    signatures = result.scalars().all()
    
    skill_errors: dict[str, int] = {}
    for sig in signatures:
        skill = sig.skill or "general"
        skill_errors[skill] = skill_errors.get(skill, 0) + sig.occurrences
    
    if not skill_errors:
        return {"reading": 0.3, "listening": 0.3, "writing": 0.2, "speaking": 0.2}
    
    max_errors = max(skill_errors.values())
    return {skill: count / max_errors for skill, count in skill_errors.items()}

async def get_recent_sessions(user_id: int, db: AsyncSession) -> list[Session]:
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.started_at.desc())
        .limit(30)
    )
    return result.scalars().all()
