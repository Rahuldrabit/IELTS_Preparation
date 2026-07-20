from typing import List
from pydantic import BaseModel, Field

class QuestionTypeConfig(BaseModel):
    """Configuration for one question type to generate."""
    type: str = Field(description="TRUE_FALSE_NOT_GIVEN | MATCHING_HEADINGS | SUMMARY_COMPLETION | MULTIPLE_CHOICE | SENTENCE_COMPLETION")
    count: int = Field(default=5, ge=1, le=10)

class GenerateReadingRequest(BaseModel):
    """User's configuration for generating a reading test."""
    difficulty: str = Field(default="intermediate", description="beginner | intermediate | advanced | ielts_6 | ielts_7 | ielts_8 | ielts_9")
    vocabulary_level: str = Field(default="academic", description="basic | medium | academic | c1 | c2")
    grammar_complexity: str = Field(default="medium", description="simple | medium | complex | mixed")
    topic: str = Field(default="technology", description="environment | science | history | technology | health | education | business | random")
    passage_length_words: int = Field(default=600, ge=300, le=1500)
    question_types: List[QuestionTypeConfig] = Field(
        default_factory=lambda: [
            QuestionTypeConfig(type="TRUE_FALSE_NOT_GIVEN", count=5),
        ]
    )

class PassageListItem(BaseModel):
    id: int
    title: str
    difficulty: str
    word_count: int

class PassageDetail(BaseModel):
    id: int
    title: str
    content: str
    word_count: int
    difficulty: str
    questions: list
