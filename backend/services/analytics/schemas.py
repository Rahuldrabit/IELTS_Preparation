from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

class ProgressWeek(BaseModel):
    week: str
    band: float
    tasks_completed: int
    time_spent: int

class BandScore(BaseModel):
    overall: float
    reading: float
    listening: float
    speaking: float
    writing: float

class SkillProgress(BaseModel):
    name: str
    progress: int

class WeeklyReport(BaseModel):
    week: str
    time_spent: int
    tasks_completed: int
    improvement: float
    skills: list[SkillProgress]

class MistakeTrend(BaseModel):
    category: str
    count: int
    week: str

class Prediction(BaseModel):
    predicted_band: float
    weeks_to_target: int
    confidence: str

class ErrorSignatureResponse(BaseModel):
    id: int
    skill: str
    question_type: Optional[str]
    error_type: Optional[str]
    pattern_label: str
    pattern_key: str
    severity: str
    occurrences: int
    example_refs: Optional[list]
    status: str
    first_seen: datetime
    last_seen: datetime

class WeeklyErrorReportResponse(BaseModel):
    id: int
    user_id: int
    week_start: date
    headline: str
    insight_text: str
    top_patterns: list[dict]
    weak_pattern_identified: str
    recommended_focus: str
    generated_at: datetime
