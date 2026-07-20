from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from . import schemas
from . import service
from . import repository

router = APIRouter(prefix="/journey", tags=["Journey"])

@router.get("/study-plan")
async def get_study_plan(
    user_id: int = 1, # Kept for consistency and future auth
    week_start: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    parsed_week_start = date.fromisoformat(week_start) if week_start else None
    plan = await service.generate_weekly_study_plan(
        user_id=user_id,
        db=db,
        week_start=parsed_week_start,
    )
    return plan.model_dump()

@router.post("/study-plan/task/complete")
async def complete_task(
    request: schemas.TaskCompletionRequest,
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    return {
        "task_id": request.task_id,
        "completed": request.completed,
        "message": "Task updated" if request.completed else "Task marked incomplete",
    }

@router.get("/streak")
async def get_streak(
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    streak = await service.calculate_streak(user_id, db)
    return {
        "streak": streak,
        "message": f"You're on a {streak}-day streak!" if streak > 0 else "Start practicing to build your streak!",
    }

@router.get("/exam-countdown")
async def get_exam_countdown(
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    user = await repository.get_user(user_id, db)
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
