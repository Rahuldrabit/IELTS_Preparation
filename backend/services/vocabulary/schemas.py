from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VocabularyCardSchema(BaseModel):
    id: int
    word: str
    pronunciation: Optional[str] = None
    meaning: Optional[str] = None
    definition: Optional[str] = None
    examples: list = []
    synonyms: list = []
    antonyms: list = []
    collocations: list = []
    word_family: list = []
    cefr: Optional[str] = None
    ielts_frequency: int = 0
    mastery: str
    next_review: Optional[str] = None

    class Config:
        from_attributes = True


class AddWordRequest(BaseModel):
    word: str


class ReviewRequest(BaseModel):
    word_id: int
    correct: bool


class VocabStats(BaseModel):
    new: int
    learning: int
    mastered: int
    total: int


class HarvestWordRequest(BaseModel):
    """Request to harvest a word from reading/listening context."""
    word: str
    context_sentence: str
    source_type: str = "reading"  # reading, listening
    source_id: Optional[int] = None  # passage_id or session_id
    paragraph_index: Optional[int] = None


class HarvestedWordResponse(BaseModel):
    """Response for a harvested vocabulary word."""
    id: int
    word: str
    context_sentence: str
    pronunciation: Optional[str] = None
    definition: Optional[str] = None
    examples: list[str] = []
    synonyms: list[str] = []
    ai_definition: Optional[str] = None  # AI-generated definition for the context
    saved_at: datetime
