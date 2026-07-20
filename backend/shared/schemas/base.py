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


# ─────────────────────────────────────────────
#  EXAM GENERATION SCHEMAS (shared by reading + listening + import)
# ─────────────────────────────────────────────

class BackendEvaluation(BaseModel):
    """
    Hidden evaluation data stored only in the DB.
    NEVER serialised into a frontend response.
    """
    correct_answer: str = Field(description="The exact correct answer string.")
    paragraph_anchor_id: str = Field(
        description="Paragraph ID (e.g. 'A', 'B') where the answer evidence lives."
    )
    evidence_text: str = Field(
        description="The verbatim sentence(s) from the passage that justify the answer."
    )
    cognitive_distractor_analysis: str = Field(
        description="Explanation of the most tempting wrong answer and why students pick it."
    )


# ─────────────────────────────────────────────
#  IMPORT SCHEMAS
# ─────────────────────────────────────────────

class ImportJobResponse(BaseModel):
    import_id: int
    status: str  # pending | processing | completed | failed | needs_questions


class ImportStatusResponse(BaseModel):
    import_id: int
    status: str
    passage_id: Optional[int] = None
    session_id: Optional[int] = None
    needs_question_generation: bool = False
    error: Optional[str] = None
