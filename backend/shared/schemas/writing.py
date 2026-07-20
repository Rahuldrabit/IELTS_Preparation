"""
Shared Pydantic schemas used across all services.

These are the canonical data contracts for:
  - Gemma 4 structured output (ExamOutput, WritingFeedback, SpeakingFeedback)
  - API request/response bodies
  - Internal service-to-service communication

Rule: BackendEvaluation is ALWAYS stripped before any response leaves the backend.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class WritingFeedback(BaseModel):
    """Structured output from Gemma 4 for essay scoring."""
    task_response: float
    coherence: float
    lexical: float
    grammar: float
    overall: float
    per_criterion_feedback: List[CriterionFeedback]
    inline_corrections: List[InlineCorrection]


class GenerateWritingTaskRequest(BaseModel):
    task_type: str = "task_2"   # task_1 | task_2
    topic: Optional[str] = None
    target_band: Optional[float] = 7.0


class WritingTaskPublic(BaseModel):
    id: int
    task_type: str
    prompt: str
    description: Optional[str] = None
    min_words: int
    band_descriptor: Optional[str] = None
    chart_data: Optional[dict] = None  # Task 1: chart/graph data for frontend rendering

    class Config:
        from_attributes = True


class WritingSubmitRequest(BaseModel):
    task_id: int
    essay: str


class WritingSubmitResponse(BaseModel):
    session_id: int
    word_count: int
    band_estimate: float
    feedback: WritingFeedback
    council_report: Optional[dict] = None
