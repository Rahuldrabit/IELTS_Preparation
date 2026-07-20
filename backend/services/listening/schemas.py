from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from shared.schemas import TTSConfig

class GenerateListeningRequest(BaseModel):
    """User's configuration for generating a listening test."""
    section: int = Field(default=1, ge=1, le=4, description="IELTS listening section 1-4")
    accent: str = Field(default="british", description="british | australian | american")
    speed: str = Field(default="normal", description="normal | exam | fast")
    topic: str = Field(default="general", description="Topic for the listening script")
    weakness_focus: List[str] = Field(default_factory=list)
    question_types: List[str] = Field(
        default_factory=lambda: ["FILL_BLANK"],
        description="Question types to generate",
    )
    question_count: int = Field(default=8, ge=4, le=12)


class DictationSegment(BaseModel):
    """A single dictation segment with target text."""
    id: int
    text: str                    # Target text for this segment
    word_count: int
    difficulty: str = "medium"   # easy | medium | hard
    order: int                   # Sequence order


class DictationContentResponse(BaseModel):
    """Response with dictation content segmented into sentences."""
    section_id: int
    session_id: int
    title: str
    total_segments: int
    segments: list[DictationSegment]
    tts_config: TTSConfig


class DictationScoreRequest(BaseModel):
    """Request for scoring a dictation attempt."""
    segment_id: int
    typed_text: str


class WordDiff(BaseModel):
    """Word-level diff result."""
    word: str
    status: str  # correct | missing | extra | substituted
    expected: Optional[str] = None
    user_input: Optional[str] = None
    is_phonetic_confusion: bool = False
    phonetic_pair: Optional[str] = None


class DictationScoreResponse(BaseModel):
    """Response with word-level scoring."""
    segment_id: int
    accuracy: float              # 0.0 - 1.0
    correct_words: int
    total_words: int
    word_diffs: list[WordDiff]
    phonetic_confusions: list[dict]


class DictationScoreFullRequest(BaseModel):
    """Request for scoring with both target and typed text."""
    segment_id: int
    session_id: int
    target_text: str
    typed_text: str


class MishearingPair(BaseModel):
    """A single mishearing pair with count."""
    expected: str
    typed: str
    count: int
    last_occurrence: datetime


class MishearingProfileResponse(BaseModel):
    """User's mishearing profile from dictation practice."""
    total_attempts: int
    total_phonetic_confusions: int
    top_confusions: list[MishearingPair]
