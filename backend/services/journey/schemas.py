from datetime import date
from typing import Optional
from pydantic import BaseModel

class TaskCompletionRequest(BaseModel):
    """Request to mark a task as complete."""
    task_id: str
    completed: bool = True

class DailyTask(BaseModel):
    """A single task for a day."""
    id: str
    day: str  # "Monday", "Tuesday", etc.
    date: date
    skill: str
    task_type: str
    title: str
    description: str
    duration_minutes: int
    priority: str = "medium"  # high, medium, low
    completed: bool = False
    linked_resource: Optional[str] = None  # URL or reference to content

class WeeklyStudyPlan(BaseModel):
    """A weekly study plan for a user."""
    user_id: int
    week_start: date
    week_end: date
    target_band: float
    days_until_exam: Optional[int] = None
    current_streak: int = 0
    tasks: list[DailyTask]
    focus_skills: list[str]  # Top 2-3 skills to focus on
    grammar_focus: Optional[str] = None
    total_minutes: int = 0
    completed_tasks: int = 0
    message: str
