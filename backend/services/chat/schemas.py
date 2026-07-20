from typing import Optional, List
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    page: str = "dashboard"
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    type: str = "message"

class DailyTask(BaseModel):
    title: str
    skill: str
    priority: str

class DailyPlan(BaseModel):
    tasks: List[DailyTask]
