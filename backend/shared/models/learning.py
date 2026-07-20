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


# ============ Vocabulary Models ============


class Vocabulary(Base):
    """User's vocabulary word."""

    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word: Mapped[str] = mapped_column(String(200), nullable=False)
    pronunciation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meaning: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examples: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    synonyms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    antonyms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    collocations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    word_family: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    cefr: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # A1-C2
    ielts_frequency: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    mastery: Mapped[str] = mapped_column(String(20), default="new")  # new, learning, mastered
    ease_factor: Mapped[float] = mapped_column(Numeric(4, 2), default=2.5)  # SM-2
    interval: Mapped[int] = mapped_column(Integer, default=1)  # days
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    first_seen: Mapped[date] = mapped_column(Date, default=date.today)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Smart Vocabulary Harvesting fields
    ai_definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Context-specific AI definition
    contexts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of {sentence, source_type, source_id}

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="vocabulary")


# ============ Daily Tasks Model ============


class DailyTask(Base):
    """Daily roadmap task for user."""

    __tablename__ = "daily_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    skill: Mapped[str] = mapped_column(String(50), nullable=False)  # reading, vocabulary, etc.
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="daily_tasks")


# ============ Milestones Model ============


class Milestone(Base):
    """User's progress milestones (band levels)."""

    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    band: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="locked"
    )  # locked, current, completed
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



# ============ Achievement Models ============


class UserAchievement(Base):
    """User's unlocked achievements."""

    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    achievement_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "band_seven", "streak_7"
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")
