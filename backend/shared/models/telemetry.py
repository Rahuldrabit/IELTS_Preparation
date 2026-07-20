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


class UserResponse(Base):
    """User's answer to a specific question."""

    __tablename__ = "user_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    reading_question_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reading_questions.id"), nullable=True
    )
    listening_question_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("listening_questions.id"), nullable=True
    )
    user_answer: Mapped[str] = mapped_column(String(1000), nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Stores per-question ExplanationResult from Gemma 4 analysis — includes why_wrong, strategy
    error_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="responses")
    reading_question: Mapped[Optional["ReadingQuestion"]] = relationship(
        "ReadingQuestion", back_populates="responses"
    )
    listening_question: Mapped[Optional["ListeningQuestion"]] = relationship(
        "ListeningQuestion", back_populates="responses"
    )


class WeeklyErrorReport(Base):
    """Weekly Error DNA report generated every Monday."""

    __tablename__ = "weekly_error_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False)  # Contains headline, insight_text, top_patterns
    signature_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of ErrorSignature IDs
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Add indexes for Error DNA


# ============ Import Queue Model ============


class ImportJob(Base):
    """Background import job for OCR processing."""

    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_type: Mapped[str] = mapped_column(String(20), nullable=False)  # reading, listening
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    file_paths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    passage_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reading_passages.id"), nullable=True
    )
    listening_section_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("listening_sections.id"), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
