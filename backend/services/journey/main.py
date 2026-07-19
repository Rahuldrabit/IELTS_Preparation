"""
Journey Service - Study plans, milestones, exam countdown.

Phase 2 Feature #5: Adaptive Study Plan
- Weekly personalized schedule
- Streak tracking
- Task completion status
"""
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

router = APIRouter(prefix="/journey", tags=["Journey"])


# ─────────────────────────────────────────────
#  Study Plan Endpoints
# ─────────────────────────────────────────────

class TaskCompletionRequest(BaseModel):
    """Request to mark a task as complete."""
    task_id: str
    completed: bool = True


@router.get("/study-plan")
async def get_study_plan(
    user_id: int = 1,
    week_start: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the weekly study plan for a user.
    
    Returns a personalized plan with daily tasks based on:
    - Weakest skills from Error DNA
    - Target exam date
    - Current progress
    """
    from services.journey.study_plan import generate_weekly_study_plan
    
    parsed_week_start = date.fromisoformat(week_start) if week_start else None
    
    plan = await generate_weekly_study_plan(
        user_id=user_id,
        db=db,
        week_start=parsed_week_start,
    )
    
    return plan.model_dump()


@router.post("/study-plan/task/complete")
async def complete_task(
    request: TaskCompletionRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a task as complete or incomplete.
    Updates the user's streak if applicable.
    """
    # In production, this would persist to a StudyTask table
    # For now, we return success
    return {
        "task_id": request.task_id,
        "completed": request.completed,
        "message": "Task updated" if request.completed else "Task marked incomplete",
    }


@router.get("/streak")
async def get_streak(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Get the user's current streak."""
    from services.journey.study_plan import _calculate_streak
    
    streak = await _calculate_streak(user_id, db)
    
    return {
        "streak": streak,
        "message": f"You're on a {streak}-day streak!" if streak > 0 else "Start practicing to build your streak!",
    }


# ─────────────────────────────────────────────
#  Exam Countdown
# ─────────────────────────────────────────────

@router.get("/exam-countdown")
async def get_exam_countdown(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Get days until the user's exam date."""
    from sqlalchemy import select
    from shared.models import User
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.exam_date:
        return {
            "has_exam_date": False,
            "days_until": None,
            "message": "Set your exam date to see a countdown",
        }
    
    days_until = (user.exam_date - date.today()).days
    
    return {
        "has_exam_date": True,
        "exam_date": user.exam_date.isoformat(),
        "days_until": days_until,
        "message": f"{days_until} days until your IELTS exam!" if days_until > 0 else "Your exam is today or has passed",
    }
