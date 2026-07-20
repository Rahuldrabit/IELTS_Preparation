import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from . import schemas
from . import repository
from . import service
from services.analytics.trajectory import calculate_band_trajectory
from services.analytics.achievements import get_achievement_summary, check_and_unlock_achievements, ACHIEVEMENTS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/progress", response_model=list[schemas.ProgressWeek])
async def get_progress(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    cached = await service.cache_get(f"analytics:progress:{user_id}")
    if cached:
        return json.loads(cached)

    user = await repository.get_user(db, user_id)
    if not user:
        return []

    progress = await service.build_progress(user)
    await service.cache_set(f"analytics:progress:{user_id}", json.dumps([p.model_dump() for p in progress]))
    return progress

@router.get("/band-scores", response_model=schemas.BandScore)
async def get_band_scores(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    cached = await service.cache_get(f"analytics:band-scores:{user_id}")
    if cached:
        return json.loads(cached)

    user = await repository.get_user(db, user_id)
    if not user:
        return schemas.BandScore(overall=6.5, reading=7.0, listening=6.5, speaking=6.0, writing=6.5)

    current = float(user.current_band)
    scores = schemas.BandScore(
        overall=current,
        reading=current + 0.5,
        listening=current,
        speaking=current - 0.5,
        writing=current,
    )
    await service.cache_set(f"analytics:band-scores:{user_id}", json.dumps(scores.model_dump()))
    return scores

@router.get("/weekly-report", response_model=schemas.WeeklyReport)
async def get_weekly_report(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    cached = await service.cache_get(f"analytics:weekly-report:{user_id}")
    if cached:
        return json.loads(cached)

    user = await repository.get_user(db, user_id)
    if not user:
        return schemas.WeeklyReport(week="This Week", time_spent=0, tasks_completed=0, improvement=0.0, skills=[])

    report = await service.build_weekly_report(user)
    await service.cache_set(f"analytics:weekly-report:{user_id}", json.dumps(report.model_dump()))
    return report

@router.get("/mistake-trends", response_model=list[schemas.MistakeTrend])
async def get_mistake_trends(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    trends = [
        schemas.MistakeTrend(category="Grammar", count=15, week="Week 1"),
        schemas.MistakeTrend(category="Vocabulary", count=12, week="Week 1"),
        schemas.MistakeTrend(category="Comprehension", count=8, week="Week 1"),
        schemas.MistakeTrend(category="Grammar", count=12, week="Week 2"),
        schemas.MistakeTrend(category="Vocabulary", count=10, week="Week 2"),
        schemas.MistakeTrend(category="Comprehension", count=6, week="Week 2"),
        schemas.MistakeTrend(category="Grammar", count=8, week="Week 3"),
        schemas.MistakeTrend(category="Vocabulary", count=7, week="Week 3"),
        schemas.MistakeTrend(category="Comprehension", count=5, week="Week 3"),
    ]
    return trends

@router.get("/predictions", response_model=schemas.Prediction)
async def get_predictions(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    cached = await service.cache_get(f"analytics:predictions:{user_id}")
    if cached:
        return json.loads(cached)

    user = await repository.get_user(db, user_id)
    if not user:
        return schemas.Prediction(predicted_band=7.0, weeks_to_target=6, confidence="medium")

    prediction = await service.build_predictions(user)
    await service.cache_set(f"analytics:predictions:{user_id}", json.dumps(prediction.model_dump()))
    return prediction

@router.get("/error-report", response_model=Optional[schemas.WeeklyErrorReportResponse])
async def get_error_report(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    report = await repository.get_latest_weekly_error_report(db, user_id)
    if not report:
        return None
    
    summary = report.summary or {}
    return schemas.WeeklyErrorReportResponse(
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

@router.get("/error-signatures", response_model=list[schemas.ErrorSignatureResponse])
async def get_error_signatures(
    user_id: int = 1,
    status: str = "active",
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    signatures = await repository.get_error_signatures(db, user_id, status, limit)
    return [
        schemas.ErrorSignatureResponse(
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
    try:
        result = await service.run_error_report_for_user(user_id, period_days, db)
        await db.commit()
        return result
    except Exception as e:
        logger.exception("Error DNA report generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trajectory")
async def get_band_trajectory(
    user_id: int = 1,
    target_band: float = 7.0,
    weeks_lookback: int = 12,
    db: AsyncSession = Depends(get_db),
):
    return await calculate_band_trajectory(
        user_id=user_id,
        db=db,
        target_band=target_band,
        weeks_lookback=weeks_lookback,
    )

@router.get("/achievements")
async def get_achievements(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    summary = await get_achievement_summary(user_id, db)
    return summary.model_dump()

@router.post("/achievements/check")
async def check_achievements(
    user_id: int = 1,
    trigger_event: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    newly_unlocked = await check_and_unlock_achievements(user_id, db, trigger_event)
    return {
        "new_unlocks": len(newly_unlocked),
        "achievements": [a.model_dump() for a in newly_unlocked],
    }

@router.get("/achievements/all")
async def list_all_achievements():
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
