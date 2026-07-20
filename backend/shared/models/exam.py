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


# ============ Reading Models ============


class ReadingPassage(Base):
    """IELTS reading passage."""

    __tablename__ = "reading_passages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy, medium, hard
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Stores GenerationParams dict from AI generation (topic, vocab_level, grammar_complexity etc.)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    questions: Mapped[list["ReadingQuestion"]] = relationship(
        "ReadingQuestion", back_populates="passage", cascade="all, delete-orphan"
    )


class ReadingQuestion(Base):
    """Individual reading question."""

    __tablename__ = "reading_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passage_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reading_passages.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # multiple-choice, true-false, fill-blank, MATCHING_HEADINGS, SUMMARY_COMPLETION etc.
    # Group ID ties this question to its QuestionGroup (e.g. "group_1")
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Sequential number within its group
    question_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # For MCQ / Matching
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Stores BackendEvaluation dict — NEVER sent to frontend
    question_evaluation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    passage: Mapped["ReadingPassage"] = relationship("ReadingPassage", back_populates="questions")
    responses: Mapped[list["UserResponse"]] = relationship(
        "UserResponse", back_populates="reading_question", cascade="all, delete-orphan"
    )


# ============ Listening Models ============


class ListeningSection(Base):
    """IELTS listening section (audio with questions)."""

    __tablename__ = "listening_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Stores GenerationParams + TTS config (accent, speed, rate)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tts_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    questions: Mapped[list["ListeningQuestion"]] = relationship(
        "ListeningQuestion", back_populates="section", cascade="all, delete-orphan"
    )


class ListeningQuestion(Base):
    """Individual listening question."""

    __tablename__ = "listening_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listening_sections.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    question_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    timestamp_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Stores BackendEvaluation dict — NEVER sent to frontend
    question_evaluation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    section: Mapped["ListeningSection"] = relationship("ListeningSection", back_populates="questions")
    responses: Mapped[list["UserResponse"]] = relationship(
        "UserResponse", back_populates="listening_question", cascade="all, delete-orphan"
    )


# ============ Writing Models ============


class WritingTask(Base):
    """IELTS writing task (Task 1 or Task 2)."""

    __tablename__ = "writing_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # task_1, task_2
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_words: Mapped[int] = mapped_column(Integer, default=150)
    band_descriptor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Stores generation params (topic, target_band)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ============ Mock Test Models ============


class MockTest(Base):
    """Full IELTS mock test session (Listening + Reading + Writing + Speaking)."""

    __tablename__ = "mock_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    test_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # baseline | generated
    status: Mapped[str] = mapped_column(
        String(20), default="in_progress"
    )  # in_progress | completed | abandoned
    # Overall results
    overall_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    listening_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    reading_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    writing_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    speaking_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    # Full AI diagnostic report JSON
    diagnostic_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Stores generated content for each section (so test can be resumed/reviewed)
    section_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mock_tests")
    sections: Mapped[list["MockTestSection"]] = relationship(
        "MockTestSection", back_populates="mock_test", cascade="all, delete-orphan",
        order_by="MockTestSection.section_order"
    )


class MockTestSection(Base):
    """Individual section within a mock test."""

    __tablename__ = "mock_test_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mock_test_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mock_tests.id", ondelete="CASCADE"), nullable=False
    )
    section_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # listening | reading | writing | speaking
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=listening, 2=reading, 3=writing, 4=speaking
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending | in_progress | completed | skipped
    # Timing
    time_allocated_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Content and answers
    content_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Generated/loaded section content
    answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # User's answers for this section
    # Scoring
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    band_estimate: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    # Per-section AI feedback
    section_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Difficulty configuration used for generation
    difficulty_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    mock_test: Mapped["MockTest"] = relationship("MockTest", back_populates="sections")


# Add indexes for performance
