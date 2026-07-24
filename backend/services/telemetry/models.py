"""
SQLAlchemy ORM models for the Cognitive Telemetry Engine.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class TelemetrySession(Base):
    """A telemetry recording session (1 per reading/listening attempt)."""

    __tablename__ = "telemetry_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    backend_session_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True
    )
    skill: Mapped[str] = mapped_column(String(20), nullable=False)  # reading | listening
    calibration_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gaze_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class TelemetrySummary(Base):
    """Aggregated telemetry metrics per upload interval (every ~2 seconds)."""

    __tablename__ = "telemetry_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telemetry_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("telemetry_sessions.id", ondelete="CASCADE"), nullable=False
    )
    paragraph_time: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fixation_count: Mapped[int] = mapped_column(Integer, default=0)
    regression_count: Mapped[int] = mapped_column(Integer, default=0)
    skip_rate: Mapped[float] = mapped_column(Float, default=0.0)
    blink_rate: Mapped[float] = mapped_column(Float, default=0.0)
    focus_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_fixation_ms: Mapped[float] = mapped_column(Float, default=0.0)
    reading_speed_wpm: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AttentionScore(Base):
    """Computed attention/focus scores for a completed session."""

    __tablename__ = "attention_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telemetry_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("telemetry_sessions.id", ondelete="CASCADE"), nullable=False
    )
    overall_attention: Mapped[float] = mapped_column(Float, default=0.0)
    scanning_efficiency: Mapped[float] = mapped_column(Float, default=0.0)
    regression_severity: Mapped[float] = mapped_column(Float, default=0.0)
    time_management: Mapped[float] = mapped_column(Float, default=0.0)
    focus_stability: Mapped[float] = mapped_column(Float, default=0.0)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QuestionBehavior(Base):
    """Per-question behavioral telemetry (computed after session)."""

    __tablename__ = "question_behavior"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telemetry_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("telemetry_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fixation_count: Mapped[int] = mapped_column(Integer, default=0)
    regression_count: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_ms: Mapped[int] = mapped_column(Integer, default=0)
    paragraph_visits: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence_signal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    answer_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)


# ─────────────────────────────────────────────
#  Indexes
# ─────────────────────────────────────────────

Index("idx_telemetry_sessions_user", TelemetrySession.user_id)
Index("idx_telemetry_sessions_backend", TelemetrySession.backend_session_id)
Index("idx_telemetry_summaries_session", TelemetrySummary.telemetry_session_id)
Index("idx_attention_scores_session", AttentionScore.telemetry_session_id)
Index("idx_question_behavior_session", QuestionBehavior.telemetry_session_id)

class UserGazeCalibration(Base):
    """Stores per-user eye calibration matrix (polynomial/affine coefficients)."""

    __tablename__ = "user_gaze_calibrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    screen_width: Mapped[int] = mapped_column(Integer, nullable=False)
    screen_height: Mapped[int] = mapped_column(Integer, nullable=False)
    device_pixel_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    calibration_matrix: Mapped[dict] = mapped_column(JSON, nullable=False)
    accuracy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

Index("idx_user_gaze_calibrations_user", UserGazeCalibration.user_id)
