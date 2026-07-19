"""
Band Score Trajectory Model - Project when user will reach target band.

Task 3: Band Score Trajectory model
- Analyzes all past sessions across skills
- Calculates improvement rate per skill
- Projects time to reach target band
- Provides confidence interval based on consistency
"""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import math

from shared.models import Session as SessionModel, User
from services.analytics.aggregation import build_cross_module_profile


# ─────────────────────────────────────────────
#  Schemas
# ─────────────────────────────────────────────

class SkillTrajectory(BaseModel):
    """Trajectory data for a single skill."""
    skill: str
    current_band: float
    target_band: float
    start_band: float  # First recorded band
    improvement_rate: float  # Band points per week
    weeks_to_target: Optional[float] = None
    confidence: float = 0.5  # 0-1 based on data consistency
    projected_date: Optional[datetime] = None
    sessions_count: int = 0
    trend: str = "stable"  # improving, stable, declining


class BandTrajectoryResponse(BaseModel):
    """Complete band score trajectory for a user."""
    user_id: int
    target_band: float
    overall_current_band: float
    overall_start_band: float
    overall_improvement_rate: float
    projected_target_date: Optional[datetime]
    confidence: float
    skill_trajectories: list[SkillTrajectory]
    message: str
    recommendations: list[str]


# ─────────────────────────────────────────────
#  Trajectory Calculation
# ─────────────────────────────────────────────

async def calculate_band_trajectory(
    user_id: int,
    db: AsyncSession,
    target_band: float = 7.0,
    weeks_lookback: int = 12,
) -> BandTrajectoryResponse:
    """
    Calculate band score trajectory for a user.
    
    Algorithm:
    1. Collect all band estimates from sessions in the lookback period
    2. Calculate improvement rate (slope of linear regression)
    3. Project time to reach target band
    4. Calculate confidence based on data consistency
    """
    now = datetime.utcnow()
    start_date = now - timedelta(weeks=weeks_lookback)
    
    # Get all sessions with band estimates
    stmt = (
        select(SessionModel)
        .where(
            and_(
                SessionModel.user_id == user_id,
                SessionModel.started_at >= start_date,
                SessionModel.band_estimate.isnot(None),
            )
        )
        .order_by(SessionModel.started_at)
    )
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    if not sessions:
        return _default_trajectory(user_id, target_band)
    
    # Group sessions by skill
    skill_sessions: dict[str, list] = {}
    for session in sessions:
        skill = session.skill or "general"
        if skill not in skill_sessions:
            skill_sessions[skill] = []
        skill_sessions[skill].append(session)
    
    # Calculate trajectory for each skill
    skill_trajectories = []
    for skill, skill_data in skill_sessions.items():
        trajectory = _calculate_skill_trajectory(skill, skill_data, target_band, now)
        skill_trajectories.append(trajectory)
    
    # Calculate overall trajectory
    overall = _calculate_overall_trajectory(sessions, target_band, now)
    
    # Generate recommendations
    recommendations = _generate_recommendations(skill_trajectories, overall, target_band)
    
    # Generate message
    message = _generate_trajectory_message(overall, target_band)
    
    return BandTrajectoryResponse(
        user_id=user_id,
        target_band=target_band,
        overall_current_band=overall["current_band"],
        overall_start_band=overall["start_band"],
        overall_improvement_rate=overall["improvement_rate"],
        projected_target_date=overall["projected_date"],
        confidence=overall["confidence"],
        skill_trajectories=skill_trajectories,
        message=message,
        recommendations=recommendations,
    )


def _calculate_skill_trajectory(
    skill: str,
    sessions: list,
    target_band: float,
    now: datetime,
) -> SkillTrajectory:
    """Calculate trajectory for a single skill."""
    if not sessions:
        return SkillTrajectory(
            skill=skill,
            current_band=0.0,
            target_band=target_band,
            start_band=0.0,
            improvement_rate=0.0,
            sessions_count=0,
        )
    
    # Extract bands and timestamps
    bands = [s.band_estimate for s in sessions if s.band_estimate]
    timestamps = [(s.started_at - sessions[0].started_at).total_seconds() / (7 * 24 * 3600) for s in sessions if s.band_estimate]
    
    if len(bands) < 2:
        return SkillTrajectory(
            skill=skill,
            current_band=bands[0] if bands else 0.0,
            target_band=target_band,
            start_band=bands[0] if bands else 0.0,
            improvement_rate=0.0,
            sessions_count=len(sessions),
            trend="stable",
        )
    
    # Linear regression for improvement rate
    n = len(bands)
    sum_x = sum(timestamps)
    sum_y = sum(bands)
    sum_xy = sum(x * y for x, y in zip(timestamps, bands))
    sum_xx = sum(x * x for x in timestamps)
    
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        improvement_rate = 0.0
    else:
        improvement_rate = (n * sum_xy - sum_x * sum_y) / denominator
    
    current_band = bands[-1]
    start_band = bands[0]
    
    # Calculate weeks to target
    gap = target_band - current_band
    if improvement_rate > 0 and gap > 0:
        weeks_to_target = gap / improvement_rate
        projected_date = now + timedelta(weeks=weeks_to_target)
    else:
        weeks_to_target = None
        projected_date = None
    
    # Calculate confidence (R-squared approximation)
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in bands)
    ss_res = sum((y - (start_band + improvement_rate * x)) ** 2 for x, y in zip(timestamps, bands))
    confidence = max(0.1, min(0.95, 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.5))
    
    # Determine trend
    if improvement_rate > 0.05:
        trend = "improving"
    elif improvement_rate < -0.05:
        trend = "declining"
    else:
        trend = "stable"
    
    return SkillTrajectory(
        skill=skill,
        current_band=round(current_band, 1),
        target_band=target_band,
        start_band=round(start_band, 1),
        improvement_rate=round(improvement_rate, 3),
        weeks_to_target=round(weeks_to_target, 1) if weeks_to_target else None,
        confidence=round(confidence, 2),
        projected_date=projected_date,
        sessions_count=len(sessions),
        trend=trend,
    )


def _calculate_overall_trajectory(
    sessions: list,
    target_band: float,
    now: datetime,
) -> dict:
    """Calculate overall trajectory across all sessions."""
    if not sessions:
        return {
            "current_band": 0.0,
            "start_band": 0.0,
            "improvement_rate": 0.0,
            "projected_date": None,
            "confidence": 0.0,
        }
    
    bands = [s.band_estimate for s in sessions if s.band_estimate]
    timestamps = [(s.started_at - sessions[0].started_at).total_seconds() / (7 * 24 * 3600) for s in sessions if s.band_estimate]
    
    if len(bands) < 2:
        return {
            "current_band": bands[0] if bands else 0.0,
            "start_band": bands[0] if bands else 0.0,
            "improvement_rate": 0.0,
            "projected_date": None,
            "confidence": 0.3,
        }
    
    # Same linear regression as skill
    n = len(bands)
    sum_x = sum(timestamps)
    sum_y = sum(bands)
    sum_xy = sum(x * y for x, y in zip(timestamps, bands))
    sum_xx = sum(x * x for x in timestamps)
    
    denominator = n * sum_xx - sum_x * sum_x
    improvement_rate = (n * sum_xy - sum_x * sum_y) / denominator if denominator != 0 else 0.0
    
    current_band = bands[-1]
    start_band = bands[0]
    
    gap = target_band - current_band
    if improvement_rate > 0 and gap > 0:
        weeks_to_target = gap / improvement_rate
        projected_date = now + timedelta(weeks=weeks_to_target)
    else:
        projected_date = None
    
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in bands)
    ss_res = sum((y - (start_band + improvement_rate * x)) ** 2 for x, y in zip(timestamps, bands))
    confidence = max(0.1, min(0.95, 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.5))
    
    return {
        "current_band": round(current_band, 1),
        "start_band": round(start_band, 1),
        "improvement_rate": round(improvement_rate, 3),
        "projected_date": projected_date,
        "confidence": round(confidence, 2),
    }


def _generate_trajectory_message(overall: dict, target_band: float) -> str:
    """Generate an encouraging message about the trajectory."""
    current = overall["current_band"]
    rate = overall["improvement_rate"]
    projected = overall["projected_date"]
    
    if rate <= 0:
        return f"You're currently at Band {current}. Keep practicing consistently to see improvement!"
    
    if projected:
        weeks = (projected - datetime.utcnow()).days / 7
        if weeks <= 2:
            return f"Great news! At your current pace, you'll reach Band {target_band} in about {max(1, int(weeks))} week(s)!"
        elif weeks <= 8:
            return f"You're making progress! Estimated {int(weeks)} weeks to Band {target_band} at this rate."
        else:
            return f"Steady improvement! At {round(rate, 2)} band points per week, you'll reach Band {target_band} in about {int(weeks)} weeks."
    
    return f"You're currently at Band {current} with a positive improvement trend. Keep it up!"


def _generate_recommendations(
    skill_trajectories: list[SkillTrajectory],
    overall: dict,
    target_band: float,
) -> list[str]:
    """Generate actionable recommendations based on trajectory analysis."""
    recommendations = []
    
    # Find weakest skills
    weak_skills = [s for s in skill_trajectories if s.current_band < overall["current_band"]]
    declining_skills = [s for s in skill_trajectories if s.trend == "declining"]
    
    if declining_skills:
        skills_str = ", ".join([s.skill for s in declining_skills[:2]])
        recommendations.append(f"Focus more on {skills_str} — these skills are declining.")
    
    if weak_skills:
        skills_str = ", ".join([s.skill for s in weak_skills[:2]])
        recommendations.append(f"Your weakest areas are {skills_str}. Target these for faster improvement.")
    
    if overall["improvement_rate"] < 0.05:
        recommendations.append("Try increasing practice frequency. Consistency is key to improvement.")
    
    if overall["confidence"] < 0.5:
        recommendations.append("Practice more regularly to get a clearer picture of your progress.")
    
    gap = target_band - overall["current_band"]
    if gap > 1.5:
        recommendations.append(f"Consider a structured study plan to bridge the {round(gap, 1)} band gap to your target.")
    
    return recommendations[:4]


def _default_trajectory(user_id: int, target_band: float) -> BandTrajectoryResponse:
    """Return default trajectory when no data available."""
    return BandTrajectoryResponse(
        user_id=user_id,
        target_band=target_band,
        overall_current_band=0.0,
        overall_start_band=0.0,
        overall_improvement_rate=0.0,
        projected_target_date=None,
        confidence=0.0,
        skill_trajectories=[],
        message="Complete some practice sessions to see your band score trajectory!",
        recommendations=["Start with a reading or listening practice to establish your baseline."],
    )
