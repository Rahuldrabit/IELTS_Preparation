"""Analytics Service - Progress, band scores, weekly report, predictions."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from shared import get_db, settings
from shared.models import User


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
        import json
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

    import json
    await cache_set("analytics:predictions", json.dumps(prediction.model_dump()))

    return prediction