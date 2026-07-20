from typing import Optional
from pydantic import BaseModel

class ShadowingModelRequest(BaseModel):
    topic: str
    part: int = 2
    accent: str = "british"
    speed: float = 0.9

class SegmentMeta(BaseModel):
    segment_id: int
    text: str
    word_count: int
    duration_estimate_ms: int
    pause_after_ms: int

class TierAudioConfig(BaseModel):
    tier: int
    band_label: str
    target_band: float
    text: str
    key_changes: list[str]
    audio_hints: str
    segments: list[SegmentMeta]
    tts_config: dict

class ShadowingModelResponse(BaseModel):
    topic: str
    part: int
    session_id: str
    mutation_tiers: list[TierAudioConfig]
    current_tier: int = 1
    pass_criteria: dict

class CreateExaminerSessionRequest(BaseModel):
    part: int = 1
    topic: Optional[str] = None

class ExaminerChatRequest(BaseModel):
    session_id: str
    message: str
    session_state: dict

class ExaminerChatResponse(BaseModel):
    session_id: str
    examiner_message: str
    follow_up_prompt: Optional[str] = None
    is_session_end: bool = False
    estimated_band: Optional[float] = None
    feedback: Optional[str] = None
    session_state: dict
