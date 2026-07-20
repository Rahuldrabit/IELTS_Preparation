from typing import Optional
from pydantic import BaseModel, Field

class SentenceEvalRequest(BaseModel):
    sentence: str
    original_sentence: str
    target_band: float = 7.0

class SentenceEvalResponse(BaseModel):
    estimated_band: float
    passes_threshold: bool
    structural_suggestions: str
    detected_grammar_features: list[str]
