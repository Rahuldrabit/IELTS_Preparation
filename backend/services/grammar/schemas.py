"""Pydantic schemas for Grammar Service."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ Base Models ============

class GrammarTopicSchema(BaseModel):
    id: int
    topic_name: str
    module: str
    description: Optional[str] = None
    order_in_module: int = 0
    prerequisites: Optional[List[int]] = None

    class Config:
        from_attributes = True


class GrammarSkillSchema(BaseModel):
    id: int
    skill_name: str
    description: Optional[str] = None
    module: Optional[str] = None
    mastery: int = 0
    confidence: float = 0.0
    mistake_count: int = 0
    recent_performance: Optional[Dict[str, Any]] = None
    last_practiced: Optional[datetime] = None
    last_reviewed: Optional[datetime] = None

    class Config:
        from_attributes = True


class GrammarMistakeSchema(BaseModel):
    id: int
    incorrect_sentence: str
    correct_sentence: str
    explanation: str
    source: Optional[str] = None
    error_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Request/Response Models ============

class DashboardResponse(BaseModel):
    overall_mastery: float
    today_accuracy: Optional[float] = None
    grammar_streak: int = 0
    weakest_topic: Optional[GrammarSkillSchema] = None
    strongest_topic: Optional[GrammarSkillSchema] = None
    daily_mission: Optional[Dict[str, Any]] = None
    weak_topics: List[GrammarSkillSchema] = []
    strong_topics: List[GrammarSkillSchema] = []
    continue_learning: Optional[Dict[str, Any]] = None


class JourneyMapResponse(BaseModel):
    total_modules: int
    total_topics: int
    modules: List[Dict[str, Any]]


class LessonContentResponse(BaseModel):
    topic_id: int
    topic_name: str
    module_id: int
    module_name: str
    description: Optional[str] = None
    rules: List[Dict[str, Any]]
    examples: Dict[str, List[str]]
    common_mistakes: List[Dict[str, Any]]


class AIExplanationRequest(BaseModel):
    level: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    language: str = Field("english", pattern="^(english|bangla)$")


class GrammarErrorAnalysisRequest(BaseModel):
    sentence: str
    context: Optional[str] = None


class GrammarErrorAnalysisResponse(BaseModel):
    category: str
    error_type: str
    explanation: str
    correct_sentence: str
    alternative_expressions: List[str] = []
    practice_recommendation: Optional[str] = None


class ExerciseGenerationRequest(BaseModel):
    types: List[str]
    count: int = Field(5, ge=1, le=20)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")


class ExerciseData(BaseModel):
    id: int
    exercise_type: str
    question_data: Dict[str, Any]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "medium"


class ExerciseSubmission(BaseModel):
    exercise_id: int
    user_answer: str


class ExerciseEvaluationResponse(BaseModel):
    is_correct: bool
    feedback: Optional[str] = None
    correct_answer: str
    explanation: Optional[str] = None
    mastery_change: int = 0


class WritingPracticeRequest(BaseModel):
    sentences: List[str]
    target_grammar: Optional[str] = None


class SentenceFeedback(BaseModel):
    sentence: str
    is_correct: bool
    grammar_feedback: str
    target_structure_used: bool
    vocabulary_notes: Optional[str] = None
    estimated_band: float = Field(ge=1.0, le=9.0)


class WritingPracticeResponse(BaseModel):
    overall_accuracy: float
    sentences_feedback: List[SentenceFeedback]
    recommendations: List[str] = []


class SpeakingPracticeRequest(BaseModel):
    target_grammar: Optional[str] = None


class SpeakingFeedback(BaseModel):
    transcript: str
    grammar_structures_found: List[str] = []
    errors_classified: List[Dict[str, Any]] = []
    feedback: str
    band_estimate: float = Field(ge=1.0, le=9.0)
    improvement_suggestions: List[str] = []


class GrammarNoteSchema(BaseModel):
    id: int
    title: str
    content: str
    mistake_pattern: Optional[str] = None
    correction: Optional[str] = None
    example: Optional[str] = None
    is_dismissed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeGraphNode(BaseModel):
    topic_id: int
    topic_name: str
    module: str
    mastery: float
    confidence: float
    recent_performance: Optional[List[float]] = None
    last_reviewed: Optional[datetime] = None
    prerequisites: List[int] = []


class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[Dict[str, Any]] = []


class AnalyticsResponse(BaseModel):
    overall_grammar: float
    today_accuracy: Optional[float] = None
    grammar_streak: int
    weakest_topic: str
    strongest_topic: str
    total_exercises_completed: int
    weekly_improvement: float = 0.0
    weekly_stats: Optional[Dict[str, Any]] = None


class Recommendation(BaseModel):
    topic_id: int
    topic_name: str
    reason: str
    priority: str = Field(pattern="^(high|medium|low)$")
    suggested_activities: List[str] = []


class RecommendationsResponse(BaseModel):
    recommendations: List[Recommendation]
    generated_at: datetime


class RecordMistakeRequest(BaseModel):
    incorrect_sentence: str
    correct_sentence: str
    explanation: str
    source: str = "writing"
    error_type: Optional[str] = None