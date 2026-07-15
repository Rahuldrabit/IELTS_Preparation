"""Profile Service - User profile, band scores, milestones, daily roadmap."""
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import User, Milestone, DailyTask


# ============ Router ============

router = APIRouter(prefix="/profile", tags=["Profile"])


# ============ Pydantic Schemas ============

class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    current_band: float
    target_band: float
    exam_date: Optional[str] = None
    daily_goal: int
    tasks_completed: int
    streak: int

    class Config:
        from_attributes = True


class BandScore(BaseModel):
    overall: float
    reading: float
    listening: float
    speaking: float
    writing: float


class MilestoneSchema(BaseModel):
    id: int
    band: float
    title: str
    description: str
    status: str
    skills: dict

    class Config:
        from_attributes = True


class DailyTaskSchema(BaseModel):
    id: int
    title: str
    skill: str
    completed: bool

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    tasks: list[DailyTaskSchema]
    completed_count: int
    total_count: int


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    target_band: Optional[float] = None
    exam_date: Optional[str] = None
    daily_goal: Optional[int] = None


# ============ Endpoints ============

@router.get("", response_model=UserProfile)
async def get_profile(db: AsyncSession = Depends(get_db)):
    """Get the current user's profile."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        current_band=float(user.current_band),
        target_band=float(user.target_band),
        exam_date=user.exam_date.isoformat() if user.exam_date else None,
        daily_goal=user.daily_goal,
        tasks_completed=user.tasks_completed,
        streak=user.streak,
    )


@router.put("", response_model=UserProfile)
async def update_profile(
    updates: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if updates.name is not None:
        user.name = updates.name
    if updates.target_band is not None:
        user.target_band = updates.target_band
    if updates.exam_date is not None:
        user.exam_date = datetime.fromisoformat(updates.exam_date).date()
    if updates.daily_goal is not None:
        user.daily_goal = updates.daily_goal

    await db.commit()
    await db.refresh(user)

    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        current_band=float(user.current_band),
        target_band=float(user.target_band),
        exam_date=user.exam_date.isoformat() if user.exam_date else None,
        daily_goal=user.daily_goal,
        tasks_completed=user.tasks_completed,
        streak=user.streak,
    )


@router.get("/band-scores", response_model=BandScore)
async def get_band_scores(db: AsyncSession = Depends(get_db)):
    """Get user's band scores across all skills."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current = float(user.current_band)
    return BandScore(
        overall=current,
        reading=current + 0.5,
        listening=current,
        speaking=current - 0.5,
        writing=current,
    )


@router.get("/milestones", response_model=list[MilestoneSchema])
async def get_milestones(db: AsyncSession = Depends(get_db)):
    """Get user's progress milestones."""
    result = await db.execute(
        select(Milestone).where(Milestone.user_id == 1).order_by(Milestone.band)
    )
    milestones = result.scalars().all()

    return [
        MilestoneSchema(
            id=m.id,
            band=float(m.band),
            title=m.title,
            description=m.description,
            status=m.status,
            skills=m.skills or {},
        )
        for m in milestones
    ]


@router.get("/roadmap", response_model=RoadmapResponse)
async def get_roadmap(db: AsyncSession = Depends(get_db)):
    """Get today's roadmap tasks."""
    today = date.today()
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.user_id == 1
        )
    )
    tasks = result.scalars().all()

    return RoadmapResponse(
        tasks=[
            DailyTaskSchema(id=t.id, title=t.title, skill=t.skill, completed=t.completed)
            for t in tasks
        ],
        completed_count=sum(1 for t in tasks if t.completed),
        total_count=len(tasks),
    )


@router.patch("/roadmap/{task_id}/complete")
async def complete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a roadmap task as complete."""
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.id == task_id,
            DailyTask.user_id == 1,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = True
    await db.commit()

    # Increment user's tasks_completed
    user_result = await db.execute(select(User).where(User.id == 1))
    user = user_result.scalar_one()
    user.tasks_completed += 1

    # Check if all tasks are complete - update streak
    today = date.today()
    all_tasks_result = await db.execute(
        select(DailyTask).where(
            DailyTask.user_id == 1,
            DailyTask.date == today,
        )
    )
    all_tasks = all_tasks_result.scalars().all()
    if all(t.completed for t in all_tasks):
        user.streak += 1

    await db.commit()

    return {"status": "completed", "task_id": task_id}