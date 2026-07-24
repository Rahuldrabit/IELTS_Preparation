"""
Pydantic schemas for the Telemetry service API.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
#  Session Schemas
# ─────────────────────────────────────────────

class TelemetrySessionCreate(BaseModel):
    user_id: int
    backend_session_id: Optional[int] = None
    skill: str = Field(description="'reading' or 'listening'")
    calibration_accuracy: Optional[float] = None
    gaze_enabled: bool = True


class TelemetrySessionResponse(BaseModel):
    id: int
    user_id: int
    skill: str
    started_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Upload Schemas
# ─────────────────────────────────────────────

class TelemetrySummaryData(BaseModel):
    """Aggregated metrics from a 2-second window."""
    paragraph_time: Dict[str, float] = Field(default_factory=dict)
    fixation_count: int = 0
    regression_count: int = 0
    skip_rate: float = 0.0
    blink_rate: float = 0.0
    focus_score: float = 0.0
    avg_fixation_ms: float = 0.0
    reading_speed_wpm: float = 0.0


class TelemetryUploadRequest(BaseModel):
    telemetry_session_id: int
    timestamp: float
    summary: Optional[TelemetrySummaryData] = None
    event_count: int = 0  # How many events this batch represents


class TelemetryUploadResponse(BaseModel):
    status: str
    events_received: int


# ─────────────────────────────────────────────
#  Event Schema (for critical single events)
# ─────────────────────────────────────────────

class TelemetryEventCreate(BaseModel):
    telemetry_session_id: int
    event_type: str
    data: Dict = Field(default_factory=dict)


# ─────────────────────────────────────────────
#  Report Schemas
# ─────────────────────────────────────────────

class AttentionScoreData(BaseModel):
    overall: float
    scanning_efficiency: float
    regression_severity: float
    time_management: float
    focus_stability: float


class TelemetryReportResponse(BaseModel):
    session_id: int
    skill: str
    duration_ms: Optional[int] = None
    total_fixations: int
    total_regressions: int
    avg_focus_score: float
    avg_fixation_ms: float
    avg_reading_speed_wpm: float
    avg_blink_rate: float
    avg_skip_rate: float
    paragraph_time: Dict[str, float] = Field(default_factory=dict)
    attention_score: Optional[AttentionScoreData] = None


# ─────────────────────────────────────────────
#  Profile Schema
# ─────────────────────────────────────────────

class TelemetryProfileResponse(BaseModel):
    user_id: int
    total_sessions: int
    avg_focus_score: float
    avg_reading_speed_wpm: float
    avg_regression_rate: float
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
#  Calibration Schemas
# ─────────────────────────────────────────────

class UserGazeCalibrationCreate(BaseModel):
    screen_width: int
    screen_height: int
    device_pixel_ratio: float = 1.0
    calibration_matrix: Dict = Field(..., description="The computed transformation matrix/coefficients")
    accuracy_score: Optional[float] = None


class UserGazeCalibrationResponse(BaseModel):
    id: int
    user_id: int
    screen_width: int
    screen_height: int
    device_pixel_ratio: float
    calibration_matrix: Dict
    accuracy_score: Optional[float]
    updated_at: datetime

    class Config:
        from_attributes = True

