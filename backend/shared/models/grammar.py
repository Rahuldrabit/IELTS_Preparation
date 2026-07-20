"""SQLAlchemy ORM models for IELTS Tutor."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


# ============ Grammar Models ============


class GrammarSkill(Base):
    """User's grammar skill mastery."""

    __tablename__ = "grammar_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Articles, Tenses, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Which module this belongs to (e.g., "Foundations", "Verb System")
    mastery: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)  # 0-1 based on performance consistency
    mistake_count: Mapped[int] = mapped_column(Integer, default=0)
    recent_performance: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Last 5 attempts: {"scores": [1,0,1,1,0], "timestamps": [...]}
    last_practiced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="grammar_skills")
    mistakes: Mapped[list["GrammarMistake"]] = relationship(
        "GrammarMistake", back_populates="skill", cascade="all, delete-orphan"
    )
    learning_history: Mapped[list["GrammarLearningHistory"]] = relationship(
        "GrammarLearningHistory", back_populates="skill", cascade="all, delete-orphan"
    )
    notes: Mapped[list["GrammarNote"]] = relationship(
        "GrammarNote", back_populates="skill", cascade="all, delete-orphan"
    )


class GrammarMistake(Base):
    """Recorded grammar mistake."""

    __tablename__ = "grammar_mistakes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grammar_skills.id", ondelete="CASCADE"), nullable=False
    )
    incorrect_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    correct_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # reading, writing, etc.
    error_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # More specific error classification
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill", back_populates="mistakes")


class GrammarTopic(Base):
    """Grammar topic structure from curriculum."""

    __tablename__ = "grammar_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)  # Which module this belongs to
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_in_module: Mapped[int] = mapped_column(Integer, default=0)  # For ordering within module
    prerequisites: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of prerequisite topic IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GrammarExercise(Base):
    """Generated grammar exercise instance."""

    __tablename__ = "grammar_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_topics.id"), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)  # fill_blank, drag_drop, etc.
    question_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Structure varies by type
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    topic: Mapped["GrammarTopic"] = relationship("GrammarTopic")


class GrammarAttempt(Base):
    """User's attempt at a grammar exercise."""

    __tablename__ = "grammar_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_exercises.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_skills.id"), nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    exercise: Mapped["GrammarExercise"] = relationship("GrammarExercise")
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill")


class GrammarNote(Base):
    """Auto-generated grammar note for repeated mistakes."""

    __tablename__ = "grammar_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_skills.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mistake_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill", back_populates="notes")


class GrammarLearningHistory(Base):
    """Track grammar learning activities."""

    __tablename__ = "grammar_learning_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_skills.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # lesson, exercise, writing_practice, speaking_practice
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill", back_populates="learning_history")


# ============ Error DNA Models ============


class ErrorSignature(Base):
    """Recurring error pattern identified by Error DNA analysis."""

    __tablename__ = "error_signatures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill: Mapped[str] = mapped_column(String(50), nullable=False)  # reading, listening, writing, speaking, grammar
    question_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # IELTS question type
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # comprehension, grammar, vocabulary
    pattern_label: Mapped[str] = mapped_column(String(200), nullable=False)  # Human-readable pattern name
    pattern_key: Mapped[str] = mapped_column(String(100), nullable=False)  # Normalized key for deduplication
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    example_refs: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of session/response IDs
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, fixed, suppressed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
