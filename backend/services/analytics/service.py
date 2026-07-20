import json
import logging
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from shared import settings
from shared.models import User, ErrorSignature, WeeklyErrorReport
from .schemas import (
    ProgressWeek, BandScore, SkillProgress, WeeklyReport,
    MistakeTrend, Prediction, WeeklyErrorReportResponse
)
from .repository import get_user, get_error_signature_by_key, create_error_signature, create_weekly_error_report, get_active_users_last_30_days

logger = logging.getLogger(__name__)

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

async def build_progress(user: User) -> list[ProgressWeek]:
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
    return progress

async def build_weekly_report(user: User) -> WeeklyReport:
    return WeeklyReport(
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

async def build_predictions(user: User) -> Prediction:
    current = float(user.current_band)
    target = float(user.target_band)

    if user.exam_date:
        days_until = (user.exam_date - datetime.now().date()).days
        weeks_until = days_until // 7
    else:
        weeks_until = 6

    band_diff = target - current
    weeks_needed = int(band_diff * 10)

    return Prediction(
        predicted_band=min(target, round(current + weeks_until * 0.1, 1)),
        weeks_to_target=weeks_needed,
        confidence="high" if weeks_needed <= weeks_until else "medium",
    )


async def run_error_report_for_user(user_id: int, period_days: int, db: AsyncSession) -> dict:
    from services.analytics.aggregation import build_cross_module_profile
    from services.agents.error_dna import ErrorDNAAgent
    
    since = datetime.utcnow() - timedelta(days=period_days)
    profile = await build_cross_module_profile(user_id, db, since)
    
    agent = ErrorDNAAgent()
    result = await agent.analyse_from_aggregation(profile)
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    signature_ids = []
    for sig in result.signatures:
        existing = await get_error_signature_by_key(db, user_id, sig.pattern_key)
        
        if existing:
            existing.occurrences += sig.occurrences
            existing.last_seen = datetime.utcnow()
            existing.severity = sig.severity
            if sig.evidence:
                existing.example_refs = sig.evidence
            existing.status = "active"
            signature_ids.append(existing.id)
        else:
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
            new_sig = await create_error_signature(db, new_sig)
            signature_ids.append(new_sig.id)
    
    report = WeeklyErrorReport(
        user_id=user_id,
        week_start=week_start,
        summary=result.model_dump(),
        signature_ids=signature_ids,
    )
    report = await create_weekly_error_report(db, report)
    
    return {
        "status": "ok",
        "report_id": report.id,
        "week_start": week_start.isoformat(),
        "signatures_count": len(result.signatures),
        "headline": result.headline,
    }


async def run_weekly_error_dna_all_users():
    from shared.database import async_session_factory
    from services.analytics.aggregation import build_cross_module_profile
    from services.agents.error_dna import ErrorDNAAgent
    
    logger.info("Starting weekly Error DNA batch job")
    
    async with async_session_factory() as db:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = await get_active_users_last_30_days(db, thirty_days_ago)
        
        logger.info(f"Found {len(active_users)} active users")
        processed = 0
        errors = 0
        
        for user in active_users:
            try:
                since = datetime.utcnow() - timedelta(days=30)
                profile = await build_cross_module_profile(user.id, db, since)
                
                if not profile.top_error_patterns:
                    continue
                
                agent = ErrorDNAAgent()
                analysis = await agent.analyse_from_aggregation(profile)
                
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                
                signature_ids = []
                for sig in analysis.signatures:
                    existing = await get_error_signature_by_key(db, user.id, sig.pattern_key)
                    
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
                        new_sig = await create_error_signature(db, new_sig)
                        signature_ids.append(new_sig.id)
                
                report = WeeklyErrorReport(
                    user_id=user.id,
                    week_start=week_start,
                    summary=analysis.model_dump(),
                    signature_ids=signature_ids,
                )
                await create_weekly_error_report(db, report)
                processed += 1
            except Exception as e:
                logger.error(f"Error DNA failed for user {user.id}: {e}")
                errors += 1
        
        await db.commit()
    
    logger.info(f"Weekly Error DNA complete: {processed} users processed, {errors} errors")
    return {"processed": processed, "errors": errors}


def register_weekly_error_dna_job():
    from shared.scheduler import register_weekly_job
    register_weekly_job(
        func=run_weekly_error_dna_all_users,
        job_id="weekly_error_dna",
        day_of_week="mon",
        hour=6,
        minute=0,
    )
    logger.info("Registered weekly Error DNA job")
