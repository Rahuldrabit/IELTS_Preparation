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


# ============ User & Profile Models ============


class User(Base):
    """User profile and preferences."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)  # Nullable for no-auth MVP
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    current_band: Mapped[float] = mapped_column(Numeric(3, 1), default=6.5)
    target_band: Mapped[float] = mapped_column(Numeric(3, 1), default=8.0)
    exam_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    daily_goal: Mapped[int] = mapped_column(Integer, default=5)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    # Stores user's feature flag preferences (JSON, nullable — defaults to all-off)
    features_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Stores the latest Uma intervention from the Autonomous Syllabus Curating Agent
    ava_intervention: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Onboarding fields ────────────────────────────────────────────────────────
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    native_language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    education_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    university_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    ielts_module: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # academic | general
    reason_for_ielts: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    focus_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # e.g. ["reading", "writing"]
    study_hours_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Subscription ─────────────────────────────────────────────────────────────
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    vocabulary: Mapped[list["Vocabulary"]] = relationship(
        "Vocabulary", back_populates="user", cascade="all, delete-orphan"
    )
    grammar_skills: Mapped[list["GrammarSkill"]] = relationship(
        "GrammarSkill", back_populates="user", cascade="all, delete-orphan"
    )
    daily_tasks: Mapped[list["DailyTask"]] = relationship(
        "DailyTask", back_populates="user", cascade="all, delete-orphan"
    )
    mock_tests: Mapped[list["MockTest"]] = relationship(
        "MockTest", back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )


# ============ Session & Response Models ============


class Session(Base):
    """Practice session (reading, listening, writing, etc.)."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill: Mapped[str] = mapped_column(String(50), nullable=False)  # reading, listening, writing, etc.
    passage_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reading_passages.id"), nullable=True
    )
    listening_section_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("listening_sections.id"), nullable=True
    )
    writing_task_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("writing_tasks.id"), nullable=True
    )
    user_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Essay text for writing
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    band_estimate: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    # Stores structured WritingFeedback or SpeakingFeedback JSON from Gemma 4
    feedback_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    responses: Mapped[list["UserResponse"]] = relationship(
        "UserResponse", back_populates="session", cascade="all, delete-orphan"
    )
