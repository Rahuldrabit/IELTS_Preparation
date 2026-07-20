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
#  LISTENING GENERATION SCHEMAS
# ─────────────────────────────────────────────

class ListeningGenerationParams(BaseModel):
    section: int = Field(ge=1, le=4, description="IELTS listening section number 1-4")
    accent: str = "british"       # british | australian | american
    speed: str = "normal"         # normal | exam | fast
    topic: str = "general"
    weakness_focus: List[str] = Field(default_factory=list)
    question_types: List[str] = Field(
        default_factory=lambda: ["FILL_BLANK"],
        description="Question types to generate"
    )
    question_count: int = Field(default=8, ge=4, le=12)


class TTSConfig(BaseModel):
    """Browser SpeechSynthesis configuration sent to frontend."""
    lang: str       # BCP-47 language tag e.g. en-GB, en-AU, en-US
    rate: float     # 0.9 normal, 1.0 exam, 1.15 fast
    pitch: float = 1.0


class GeneratedListeningResponse(BaseModel):
    """Response returned to frontend after /listening/generate."""
    section_id: int
    session_id: int
    title: str
    script: str                          # Full transcript for browser TTS
    tts_config: TTSConfig
    question_groups: List[QuestionGroupPublic]
    generation_params: Optional[dict] = None


# ─────────────────────────────────────────────
#  SPEAKING SCHEMAS
# ─────────────────────────────────────────────

class SpeakingFeedback(BaseModel):
    """Structured output from Gemma 4 for speaking analysis."""
    transcript: str
    band: float
    fluency: float
    lexical: float
    grammar: float
    pronunciation: float
    suggestions: List[str]
