"""Grammar Service - Grammar topics, mistakes, mastery, AI exercise generation."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from shared import get_db
from shared.models import GrammarSkill, GrammarMistake


# ============ Router ============

router = APIRouter(prefix="/grammar", tags=["Grammar"])


# ============ Pydantic Schemas ============

class GrammarTopicSchema(BaseModel):
    id: int
    skill_name: str
    description: Optional[str] = None
    mastery: int
    mistake_count: int
    last_practiced: Optional[str] = None

    class Config:
        from_attributes = True


class GrammarMistakeSchema(BaseModel):
    id: int
    incorrect_sentence: str
    correct_sentence: str
    explanation: str
    date: str

    class Config:
        from_attributes = True


class GrammarTopicDetail(GrammarTopicSchema):
    mistakes: list[GrammarMistakeSchema] = []


class RecordMistakeRequest(BaseModel):
    incorrect_sentence: str
    correct_sentence: str
    explanation: str
    source: str = "writing"


class ExerciseSubmission(BaseModel):
    exercise_id: int
    user_answer: str


# ============ Endpoints ============

@router.get("/topics")
async def get_topics(db: AsyncSession = Depends(get_db)):
    """Get all grammar topics."""
    result = await db.execute(
        select(GrammarSkill)
        .where(GrammarSkill.user_id == 1)
        .order_by(GrammarSkill.mistake_count.desc())
    )
    topics = result.scalars().all()

    return [
        GrammarTopicSchema(
            id=t.id,
            skill_name=t.skill_name,
            description=t.description,
            mastery=t.mastery,
            mistake_count=t.mistake_count,
            last_practiced=t.last_practiced.isoformat() if t.last_practiced else None,
        )
        for t in topics
    ]


@router.get("/topics/{topic_id}")
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific grammar topic with mistakes."""
    result = await db.execute(
        select(GrammarSkill)
        .where(GrammarSkill.id == topic_id)
        .where(GrammarSkill.user_id == 1)
    )
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    mistakes_result = await db.execute(
        select(GrammarMistake)
        .where(GrammarMistake.skill_id == topic_id)
        .order_by(GrammarMistake.created_at.desc())
    )
    mistakes = mistakes_result.scalars().all()

    return GrammarTopicDetail(
        id=topic.id,
        skill_name=topic.skill_name,
        description=topic.description,
        mastery=topic.mastery,
        mistake_count=topic.mistake_count,
        last_practiced=topic.last_practiced.isoformat() if topic.last_practiced else None,
        mistakes=[
            GrammarMistakeSchema(
                id=m.id,
                incorrect_sentence=m.incorrect_sentence,
                correct_sentence=m.correct_sentence,
                explanation=m.explanation,
                date=m.created_at.isoformat(),
            )
            for m in mistakes
        ],
    )


@router.post("/topics/{topic_id}/record-mistake")
async def record_mistake(
    topic_id: int,
    request: RecordMistakeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record a new grammar mistake."""
    result = await db.execute(
        select(GrammarSkill)
        .where(GrammarSkill.id == topic_id)
        .where(GrammarSkill.user_id == 1)
    )
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    mistake = GrammarMistake(
        skill_id=topic_id,
        incorrect_sentence=request.incorrect_sentence,
        correct_sentence=request.correct_sentence,
        explanation=request.explanation,
        source=request.source,
    )
    db.add(mistake)

    topic.mistake_count += 1
    topic.mastery = max(0, topic.mastery - 2)
    topic.last_practiced = datetime.utcnow()

    await db.commit()

    return {"status": "recorded", "mistake_id": mistake.id}


@router.post("/topics/{topic_id}/exercises")
async def generate_exercises(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Generate AI-powered grammar exercises."""
    result = await db.execute(
        select(GrammarSkill)
        .where(GrammarSkill.id == topic_id)
        .where(GrammarSkill.user_id == 1)
    )
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    mistakes_result = await db.execute(
        select(GrammarMistake)
        .where(GrammarMistake.skill_id == topic_id)
        .order_by(GrammarMistake.created_at.desc())
        .limit(5)
    )
    mistakes = mistakes_result.scalars().all()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/agent/generate-exercises",
                json={
                    "topic": topic.skill_name,
                    "mistakes": [
                        {"incorrect": m.incorrect_sentence, "correct": m.correct_sentence}
                        for m in mistakes
                    ],
                },
            )
            response.raise_for_status()
            exercises = response.json()
        except:
            exercises = {"exercises": []}

    return exercises


@router.post("/topics/{topic_id}/exercises/submit")
async def submit_exercises(
    topic_id: int,
    submissions: list[ExerciseSubmission],
    db: AsyncSession = Depends(get_db),
):
    """Submit exercise answers and update mastery."""
    result = await db.execute(
        select(GrammarSkill)
        .where(GrammarSkill.id == topic_id)
        .where(GrammarSkill.user_id == 1)
    )
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    total = len(submissions)
    correct_count = total  # Simplified - would need actual evaluation

    if total > 0:
        score = correct_count / total
        mastery_increase = int(score * 5)
        topic.mastery = min(100, topic.mastery + mastery_increase)

    topic.last_practiced = datetime.utcnow()

    await db.commit()

    return {
        "status": "completed",
        "correct": correct_count,
        "total": total,
        "new_mastery": topic.mastery,
    }