"""Analytics Service - Progress, band scores, weekly report, predictions, Error DNA."""
from datetime import datetime, date, timedelta
from typing import Optional
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from shared import get_db, settings
from shared.models import User, Session, ErrorSignature, WeeklyErrorReport

logger = logging.getLogger(__name__)


# ============ Router ============

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ============ Pydantic Schemas ============

class ProgressWeek(BaseModel):
    week: str
    band: float
    tasks_completed: int
    time_spent: int


class BandScore(BaseModel):
    overall: float
    reading: float
    listening: float
    speaking: float
    writing: float


class SkillProgress(BaseModel):
    name: str
    progress: int


class WeeklyReport(BaseModel):
    week: str
    time_spent: int
    tasks_completed: int
    improvement: float
    skills: list[SkillProgress]


class MistakeTrend(BaseModel):
    category: str
    count: int
    week: str


class Prediction(BaseModel):
    predicted_band: float
    weeks_to_target: int
    confidence: str


# ============ Redis Helper ============

_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def cache_get(key: str) -> Optional[str]:
    try:
        r = await get_redis()
        return await r.get(key)
    except:
        return None


async def cache_set(key: str, value: str, ttl: int = 300):
    try:
        r = await get_redis()
        await r.setex(key, ttl, value)
    except:
        pass


# ============ Endpoints ============

@router.get("/progress")
async def get_progress(db: AsyncSession = Depends(get_db)):
    """Get weekly band progress."""
    cached = await cache_get("analytics:progress")
    if cached:
        import json
        return json.loads(cached)

    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        return []

    current = float(user.current_band)
    progress = []

    for i in range(6, 0, -1):
        band = round(current - (i * 0.1), 1)
        progress.append(
            ProgressWeek(
                week=f"Week {7 - i}",
                band=max(5.5, band),
                tasks_completed=10 + (6 - i) * 3,
                time_spent=180 + (6 - i) * 15,
            )
        )

    progress.append(
        ProgressWeek(
            week="This Week",
            band=current,
            tasks_completed=user.tasks_completed,
            time_spent=user.tasks_completed * 30,
        )
    )

    import json
    await cache_set("analytics:progress", json.dumps([p.model_dump() for p in progress]))

    return progress


@router.get("/band-scores")
async def get_band_scores(db: AsyncSession = Depends(get_db)):
    """Get current band scores per skill."""
    cached = await cache_get("analytics:band-scores")
    if cached:
        import json
        return json.loads(cached)

    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        return BandScore(overall=6.5, reading=7.0, listening=6.5, speaking=6.0, writing=6.5)

    current = float(user.current_band)

    scores = BandScore(
        overall=current,
        reading=current + 0.5,
        listening=current,
        speaking=current - 0.5,
        writing=current,
    )

    import json
    await cache_set("analytics:band-scores", json.dumps(scores.model_dump()))

    return scores


@router.get("/weekly-report")
async def get_weekly_report(db: AsyncSession = Depends(get_db)):
    """Get weekly report."""
    cached = await cache_get("analytics:weekly-report")
    if cached:
        import json
        return json.loads(cached)

    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        return WeeklyReport(week="This Week", time_spent=0, tasks_completed=0, improvement=0.0, skills=[])

    report = WeeklyReport(
        week="This Week",
        time_spent=user.tasks_completed * 30,
        tasks_completed=user.tasks_completed,
        improvement=0.2,
        skills=[
            SkillProgress(name="Reading", progress=5),
            SkillProgress(name="Listening", progress=3),
            SkillProgress(name="Speaking", progress=2),
            SkillProgress(name="Writing", progress=4),
        ],
    )

    import json
    await cache_set("analytics:weekly-report", json.dumps(report.model_dump()))

    return report


@router.get("/mistake-trends")
async def get_mistake_trends(db: AsyncSession = Depends(get_db)):
    """Get mistake trends by category."""
    trends = [
        MistakeTrend(category="Grammar", count=15, week="Week 1"),
        MistakeTrend(category="Vocabulary", count=12, week="Week 1"),
        MistakeTrend(category="Comprehension", count=8, week="Week 1"),
        MistakeTrend(category="Grammar", count=12, week="Week 2"),
        MistakeTrend(category="Vocabulary", count=10, week="Week 2"),
        MistakeTrend(category="Comprehension", count=6, week="Week 2"),
        MistakeTrend(category="Grammar", count=8, week="Week 3"),
        MistakeTrend(category="Vocabulary", count=7, week="Week 3"),
        MistakeTrend(category="Comprehension", count=5, week="Week 3"),
    ]
    return trends


@router.get("/predictions")
async def get_predictions(db: AsyncSession = Depends(get_db)):
    """Get band score prediction."""
    cached = await cache_get("analytics:predictions")
    if cached:
        return json.loads(cached)

    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        return Prediction(predicted_band=7.0, weeks_to_target=6, confidence="medium")

    current = float(user.current_band)
    target = float(user.target_band)

    if user.exam_date:
        days_until = (user.exam_date - datetime.now().date()).days
        weeks_until = days_until // 7
    else:
        weeks_until = 6

    band_diff = target - current
    weeks_needed = int(band_diff * 10)

    prediction = Prediction(
        predicted_band=min(target, round(current + weeks_until * 0.1, 1)),
        weeks_to_target=weeks_needed,
        confidence="high" if weeks_needed <= weeks_until else "medium",
    )

    await cache_set("analytics:predictions", json.dumps(prediction.model_dump()))

    return prediction


# ─────────────────────────────────────────────
#  Error DNA Report Endpoints
# ─────────────────────────────────────────────

class ErrorSignatureResponse(BaseModel):
    """Error signature for API response."""
    id: int
    skill: str
    question_type: Optional[str]
    error_type: Optional[str]
    pattern_label: str
    pattern_key: str
    severity: str
    occurrences: int
    example_refs: Optional[list]
    status: str
    first_seen: datetime
    last_seen: datetime


class WeeklyErrorReportResponse(BaseModel):
    """Weekly Error DNA report for API response."""
    id: int
    user_id: int
    week_start: date
    headline: str
    insight_text: str
    top_patterns: list[dict]
    weak_pattern_identified: str
    recommended_focus: str
    generated_at: datetime


@router.get("/error-report", response_model=Optional[WeeklyErrorReportResponse])
async def get_error_report(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Get the latest weekly Error DNA report for a user."""
    result = await db.execute(
        select(WeeklyErrorReport)
        .where(WeeklyErrorReport.user_id == user_id)
        .order_by(WeeklyErrorReport.week_start.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        return None
    
    summary = report.summary or {}
    
    return WeeklyErrorReportResponse(
        id=report.id,
        user_id=report.user_id,
        week_start=report.week_start,
        headline=summary.get("headline", ""),
        insight_text=summary.get("insight_text", ""),
        top_patterns=summary.get("signatures", []),
        weak_pattern_identified=summary.get("weak_pattern_identified", ""),
        recommended_focus=summary.get("recommended_focus", ""),
        generated_at=report.generated_at,
    )


@router.get("/error-signatures", response_model=list[ErrorSignatureResponse])
async def get_error_signatures(
    user_id: int = 1,
    status: str = "active",
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get error signatures for a user."""
    result = await db.execute(
        select(ErrorSignature)
        .where(and_(
            ErrorSignature.user_id == user_id,
            ErrorSignature.status == status,
        ))
        .order_by(ErrorSignature.occurrences.desc())
        .limit(limit)
    )
    signatures = result.scalars().all()
    
    return [
        ErrorSignatureResponse(
            id=s.id,
            skill=s.skill,
            question_type=s.question_type,
            error_type=s.error_type,
            pattern_label=s.pattern_label,
            pattern_key=s.pattern_key,
            severity=s.severity,
            occurrences=s.occurrences,
            example_refs=s.example_refs,
            status=s.status,
            first_seen=s.first_seen,
            last_seen=s.last_seen,
        )
        for s in signatures
    ]


@router.post("/error-report/run")
async def run_error_report(
    user_id: int = 1,
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger Error DNA analysis for a user.
    Persists the results to WeeklyErrorReport and ErrorSignature tables.
    """
    from services.analytics.aggregation import build_cross_module_profile
    from services.agents.error_dna import ErrorDNAAgent
    
    try:
        # Build error profile
        since = datetime.utcnow() - timedelta(days=period_days)
        profile = await build_cross_module_profile(user_id, db, since)
        
        # Run Error DNA analysis
        agent = ErrorDNAAgent()
        result = await agent.analyse_from_aggregation(profile)
        
        # Determine week start (Monday of current week)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        # Store signatures
        signature_ids = []
        for sig in result.signatures:
            # Check if signature already exists
            existing_result = await db.execute(
                select(ErrorSignature).where(and_(
                    ErrorSignature.user_id == user_id,
                    ErrorSignature.pattern_key == sig.pattern_key,
                ))
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                # Update existing signature
                existing.occurrences += sig.occurrences
                existing.last_seen = datetime.utcnow()
                existing.severity = sig.severity
                if sig.evidence:
                    existing.example_refs = sig.evidence
                existing.status = "active"
                signature_ids.append(existing.id)
            else:
                # Create new signature
                new_sig = ErrorSignature(
                    user_id=user_id,
                    skill=sig.skill,
                    question_type=sig.question_type,
                    error_type=sig.error_type,
                    pattern_label=sig.pattern_label,
                    pattern_key=sig.pattern_key,
                    severity=sig.severity,
                    occurrences=sig.occurrences,
                    example_refs=sig.evidence,
                    status="active",
                )
                db.add(new_sig)
                await db.flush()
                signature_ids.append(new_sig.id)
        
        # Store weekly report
        report = WeeklyErrorReport(
            user_id=user_id,
            week_start=week_start,
            summary=result.model_dump(),
            signature_ids=signature_ids,
        )
        db.add(report)
        
        await db.commit()
        await db.refresh(report)
        
        return {
            "status": "ok",
            "report_id": report.id,
            "week_start": week_start.isoformat(),
            "signatures_count": len(result.signatures),
            "headline": result.headline,
        }
        
    except Exception as e:
        logger.exception("Error DNA report generation failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
#  Weekly Batch Job
# ─────────────────────────────────────────────

async def run_weekly_error_dna_all_users():
    """
    Weekly batch job that runs Error DNA for all active users.
    Called by the scheduler every Monday at 6 AM.
    """
    from shared.database import async_session_factory
    from services.analytics.aggregation import build_cross_module_profile
    from services.agents.error_dna import ErrorDNAAgent
    
    logger.info("Starting weekly Error DNA batch job")
    
    async with async_session_factory() as db:
        # Get all users with sessions in the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        result = await db.execute(
            select(User)
            .join(User.sessions)
            .where(Session.started_at >= thirty_days_ago)
            .distinct()
        )
        active_users = result.scalars().all()
        
        logger.info(f"Found {len(active_users)} active users")
        
        processed = 0
        errors = 0
        
        for user in active_users:
            try:
                # Build error profile
                since = datetime.utcnow() - timedelta(days=30)
                profile = await build_cross_module_profile(user.id, db, since)
                
                # Skip if no errors
                if not profile.top_error_patterns:
                    continue
                
                # Run analysis
                agent = ErrorDNAAgent()
                analysis = await agent.analyse_from_aggregation(profile)
                
                # Determine week start
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                
                # Store signatures (upsert logic)
                signature_ids = []
                for sig in analysis.signatures:
                    existing_result = await db.execute(
                        select(ErrorSignature).where(and_(
                            ErrorSignature.user_id == user.id,
                            ErrorSignature.pattern_key == sig.pattern_key,
                        ))
                    )
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        existing.occurrences += sig.occurrences
                        existing.last_seen = datetime.utcnow()
                        existing.severity = sig.severity
                        existing.status = "active"
                        signature_ids.append(existing.id)
                    else:
                        new_sig = ErrorSignature(
                            user_id=user.id,
                            skill=sig.skill,
                            question_type=sig.question_type,
                            error_type=sig.error_type,
                            pattern_label=sig.pattern_label,
                            pattern_key=sig.pattern_key,
                            severity=sig.severity,
                            occurrences=sig.occurrences,
                            example_refs=sig.evidence,
                            status="active",
                        )
                        db.add(new_sig)
                        await db.flush()
                        signature_ids.append(new_sig.id)
                
                # Store weekly report
                report = WeeklyErrorReport(
                    user_id=user.id,
                    week_start=week_start,
                    summary=analysis.model_dump(),
                    signature_ids=signature_ids,
                )
                db.add(report)
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error DNA failed for user {user.id}: {e}")
                errors += 1
        
        await db.commit()
    
    logger.info(f"Weekly Error DNA complete: {processed} users processed, {errors} errors")
    return {"processed": processed, "errors": errors}


def register_weekly_error_dna_job():
    """Register the weekly Error DNA job with the scheduler."""
    from shared.scheduler import register_weekly_job
    
    register_weekly_job(
        func=run_weekly_error_dna_all_users,
        job_id="weekly_error_dna",
        day_of_week="mon",
        hour=6,
        minute=0,
    )
    logger.info("Registered weekly Error DNA job")



# ─────────────────────────────────────────────
#  Band Score Trajectory (Phase 2 Feature #4)
# ─────────────────────────────────────────────

@router.get("/trajectory")
async def get_band_trajectory(
    user_id: int = 1,
    target_band: float = 7.0,
    weeks_lookback: int = 12,
    db: AsyncSession = Depends(get_db),
):
    """
    Get band score trajectory projection for a user.
    
    Uses linear regression on past session band estimates to predict
    when the user will reach their target band score.
    
    Returns:
    - Current band estimate
    - Improvement rate (band points per week)
    - Projected date to reach target
    - Confidence level (based on data consistency)
    - Per-skill breakdown
    """
    from services.analytics.trajectory import calculate_band_trajectory
    
    return await calculate_band_trajectory(
        user_id=user_id,
        db=db,
        target_band=target_band,
        weeks_lookback=weeks_lookback,
    )



# ─────────────────────────────────────────────
#  Achievements System (Phase 3 Feature #9)
# ─────────────────────────────────────────────

@router.get("/achievements")
async def get_achievements(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's achievement summary.
    
    Returns unlocked achievements, progress toward locked ones,
    and statistics by category and tier.
    """
    from services.analytics.achievements import get_achievement_summary
    
    summary = await get_achievement_summary(user_id, db)
    return summary.model_dump()


@router.post("/achievements/check")
async def check_achievements(
    user_id: int = 1,
    trigger_event: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Check and unlock new achievements.
    
    Called automatically after key events like:
    - Completing a session
    - Reaching a band score
    - Maintaining a streak
    
    Returns list of newly unlocked achievements.
    """
    from services.analytics.achievements import check_and_unlock_achievements
    
    newly_unlocked = await check_and_unlock_achievements(user_id, db, trigger_event)
    
    return {
        "new_unlocks": len(newly_unlocked),
        "achievements": [a.model_dump() for a in newly_unlocked],
    }


@router.get("/achievements/all")
async def list_all_achievements():
    """Get list of all possible achievements."""
    from services.analytics.achievements import ACHIEVEMENTS
    
    return {
        "achievements": [
            {
                "id": aid,
                **achievement,
            }
            for aid, achievement in ACHIEVEMENTS.items()
        ],
        "total": len(ACHIEVEMENTS),
    }
