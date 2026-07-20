from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class MockTestSectionResponse(BaseModel):
    id: int
    section_type: str
    section_order: int
    status: str
    time_allocated_seconds: int
    time_spent_seconds: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    band_estimate: Optional[float] = None
    difficulty_config: Optional[list | dict] = None

    class Config:
        from_attributes = True

class MockTestResponse(BaseModel):
    id: int
    test_type: str
    status: str
    overall_band: Optional[float] = None
    listening_band: Optional[float] = None
    reading_band: Optional[float] = None
    writing_band: Optional[float] = None
    speaking_band: Optional[float] = None
    started_at: str
    finished_at: Optional[str] = None
    total_time_seconds: Optional[int] = None
    sections: List[MockTestSectionResponse] = []

    class Config:
        from_attributes = True

class MockTestHistoryItem(BaseModel):
    id: int
    test_type: str
    status: str
    overall_band: Optional[float] = None
    listening_band: Optional[float] = None
    reading_band: Optional[float] = None
    writing_band: Optional[float] = None
    speaking_band: Optional[float] = None
    started_at: str
    finished_at: Optional[str] = None
    total_time_seconds: Optional[int] = None

class MockTestDetailResponse(BaseModel):
    id: int
    test_type: str
    status: str
    overall_band: Optional[float] = None
    listening_band: Optional[float] = None
    reading_band: Optional[float] = None
    writing_band: Optional[float] = None
    speaking_band: Optional[float] = None
    started_at: str
    finished_at: Optional[str] = None
    total_time_seconds: Optional[int] = None
    sections: List[dict] = []
    diagnostic_report: Optional[dict] = None

class SectionSubmitRequest(BaseModel):
    answers: dict = Field(description="User answers for this section")
    time_spent_seconds: int = Field(description="Time spent on this section in seconds")

class StartMockTestRequest(BaseModel):
    test_type: Optional[str] = Field(
        default=None,
        description="Force 'baseline' or 'generated'. Auto-detects if None."
    )
