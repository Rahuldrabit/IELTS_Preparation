from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

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
    onboarding_completed: bool
    native_language: Optional[str] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None  # high_school | bachelors | masters | phd
    ielts_module: Optional[str] = None  # academic | general
    reason_for_ielts: Optional[str] = None  # immigration | university | career | other
    focus_skills: Optional[list[str]] = None  # ["reading", "writing", "listening", "speaking"]
    study_hours_per_day: Optional[int] = None

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


class SkillFeaturesUpdate(BaseModel):
    reading: Optional[dict] = None
    writing: Optional[dict] = None
    listening: Optional[dict] = None
    speaking: Optional[dict] = None


class JourneyRecommendation(BaseModel):
    skill: str
    topic: str
    difficulty: str
    question_type: str
    reason: str


class OnboardingRequest(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    native_language: Optional[str] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None
    current_band: Optional[float] = None
    target_band: Optional[float] = None
    exam_date: Optional[str] = None
    ielts_module: Optional[str] = None
    reason_for_ielts: Optional[str] = None
    focus_skills: Optional[list[str]] = None
    study_hours_per_day: Optional[int] = None
    daily_goal: Optional[int] = None


class PersonalizedPlan(BaseModel):
    weekly_focus: list[str]
    skill_priorities: list[dict]
    study_schedule_suggestion: str
    motivational_message: str
    estimated_weeks_to_target: Optional[int] = None


class OnboardingResponse(BaseModel):
    success: bool
    plan: PersonalizedPlan
