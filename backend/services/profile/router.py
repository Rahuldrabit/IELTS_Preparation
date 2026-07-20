import asyncio
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared import get_db
from shared.models import User, Milestone, DailyTask
from services.agents.syllabus import SyllabusCuratorAgent, SkillTelemetrySummary
from services.llm import LLMClientError

from . import schemas
from . import repository
from . import service

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=schemas.UserProfile)
async def get_profile(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        current_band=float(user.current_band),
        target_band=float(user.target_band),
        exam_date=user.exam_date.isoformat() if user.exam_date else None,
        daily_goal=user.daily_goal,
        tasks_completed=user.tasks_completed,
        streak=user.streak,
        onboarding_completed=user.onboarding_completed,
        native_language=user.native_language,
        occupation=user.occupation,
        education_level=user.education_level,
        ielts_module=user.ielts_module,
        reason_for_ielts=user.reason_for_ielts,
        focus_skills=user.focus_skills,
        study_hours_per_day=user.study_hours_per_day,
    )


@router.put("", response_model=schemas.UserProfile)
async def update_profile(
    updates: schemas.UpdateProfileRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if updates.name is not None:
        user.name = updates.name
    if updates.target_band is not None:
        user.target_band = updates.target_band
    if updates.exam_date is not None:
        user.exam_date = datetime.fromisoformat(updates.exam_date).date()
    if updates.daily_goal is not None:
        user.daily_goal = updates.daily_goal

    await db.commit()
    await db.refresh(user)

    return schemas.UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        current_band=float(user.current_band),
        target_band=float(user.target_band),
        exam_date=user.exam_date.isoformat() if user.exam_date else None,
        daily_goal=user.daily_goal,
        tasks_completed=user.tasks_completed,
        streak=user.streak,
        onboarding_completed=user.onboarding_completed,
    )


@router.get("/band-scores", response_model=schemas.BandScore)
async def get_band_scores(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current = float(user.current_band)
    return schemas.BandScore(
        overall=current,
        reading=current + 0.5,
        listening=current,
        speaking=current - 0.5,
        writing=current,
    )


@router.get("/milestones", response_model=list[schemas.MilestoneSchema])
async def get_milestones(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    milestones = await repository.get_user_milestones(db, user_id)
    return [
        schemas.MilestoneSchema(
            id=m.id,
            band=float(m.band),
            title=m.title,
            description=m.description,
            status=m.status,
            skills=m.skills or {},
        )
        for m in milestones
    ]


@router.get("/roadmap", response_model=schemas.RoadmapResponse)
async def get_roadmap(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    today = date.today()
    tasks = await repository.get_daily_tasks(db, user_id, today)

    if not tasks:
        all_tasks = await repository.get_all_daily_tasks(db, user_id)
        for t in all_tasks:
            t.date = today
            t.completed = False
        await db.commit()
        tasks = all_tasks

    return schemas.RoadmapResponse(
        tasks=[
            schemas.DailyTaskSchema(id=t.id, title=t.title, skill=t.skill, completed=t.completed)
            for t in tasks
        ],
        completed_count=sum(1 for t in tasks if t.completed),
        total_count=len(tasks),
    )


@router.patch("/roadmap/{task_id}/complete")
async def complete_task(task_id: int, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    task = await repository.get_daily_task_by_id(db, task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = True
    
    user = await repository.get_user(db, user_id)
    if user:
        user.tasks_completed += 1

    today = date.today()
    all_tasks = await repository.get_daily_tasks(db, user_id, today)
    if all(t.completed for t in all_tasks) and user:
        user.streak += 1

    await db.commit()
    return {"status": "completed", "task_id": task_id}


@router.get("/features")
async def get_features(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return service.merge_features(user.features_config or {})


@router.patch("/features")
async def update_features(
    updates: schemas.SkillFeaturesUpdate,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = dict(user.features_config or {})
    payload = updates.model_dump(exclude_none=True)
    for skill, vals in payload.items():
        if vals:
            existing.setdefault(skill, {}).update(vals)

    user.features_config = existing
    await db.commit()
    return service.merge_features(existing)


@router.get("/uma-intervention")
async def get_uma_intervention(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.ava_intervention or None


@router.post("/uma-intervention/refresh")
async def refresh_uma_intervention(
    telemetry: dict,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        summary = SkillTelemetrySummary(
            reading_band=telemetry.get("reading_band", float(user.current_band)),
            reading_sessions=telemetry.get("reading_sessions", 0),
            reading_wrong_question_types=telemetry.get("reading_wrong_question_types", []),
            reading_avg_time_per_question_ms=telemetry.get("reading_avg_time_per_question_ms", 0),
            reading_low_confidence_wins=telemetry.get("reading_low_confidence_wins", 0),
            reading_passage_friction_avg=telemetry.get("reading_passage_friction_avg", 0),
            writing_band=telemetry.get("writing_band", float(user.current_band)),
            writing_sessions=telemetry.get("writing_sessions", 0),
            writing_weak_criteria=telemetry.get("writing_weak_criteria", []),
            listening_band=telemetry.get("listening_band", float(user.current_band)),
            listening_sessions=telemetry.get("listening_sessions", 0),
            listening_avg_seek_count=telemetry.get("listening_avg_seek_count", 0),
            speaking_band=telemetry.get("speaking_band", float(user.current_band)),
            speaking_sessions=telemetry.get("speaking_sessions", 0),
            speaking_filler_count_avg=telemetry.get("speaking_filler_count_avg", 0),
            target_band=float(user.target_band),
            exam_date_days_remaining=(
                (user.exam_date - date.today()).days if user.exam_date else None
            ),
        )

        agent = SyllabusCuratorAgent()
        intervention = await agent.analyse(summary)
        user.ava_intervention = intervention.model_dump()
        await db.commit()
        return user.ava_intervention
    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Syllabus analysis failed: {str(e)}")


_DIFFICULTY_MAP = {
    "TRUE_FALSE_NOT_GIVEN": "intermediate",
    "MATCHING_HEADINGS": "advanced",
    "SUMMARY_COMPLETION": "intermediate",
    "MULTIPLE_CHOICE": "intermediate",
    "SENTENCE_COMPLETION": "intermediate",
}

@router.get("/journey-recommendation", response_model=schemas.JourneyRecommendation)
async def get_journey_recommendation(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    intervention = user.ava_intervention
    if intervention:
        skill = intervention.get("targeted_skill", "reading")
        topic = intervention.get("drill_topic", "general")
        question_type = intervention.get("drill_question_type", "MULTIPLE_CHOICE")
        difficulty = _DIFFICULTY_MAP.get(question_type, "intermediate")
        reason = intervention.get("insight_text", "Based on your recent performance analysis.")
        return schemas.JourneyRecommendation(
            skill=skill,
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            reason=reason,
        )

    focus_skills = user.focus_skills or []
    skill = focus_skills[0] if focus_skills else "reading"

    defaults = {
        "reading": ("technology", "TRUE_FALSE_NOT_GIVEN"),
        "writing": ("education", "TASK_2_ESSAY"),
        "listening": ("daily life", "FILL_BLANK"),
        "speaking": ("hobbies", "PART_2_CUE_CARD"),
    }
    topic, question_type = defaults.get(skill, ("general", "MULTIPLE_CHOICE"))

    return schemas.JourneyRecommendation(
        skill=skill,
        topic=topic,
        difficulty="intermediate",
        question_type=question_type,
        reason=f"Starting with {skill} based on your study preferences.",
    )


@router.get("/onboarding-status")
async def get_onboarding_status(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"completed": user.onboarding_completed}


@router.post("/onboarding", response_model=schemas.OnboardingResponse)
async def submit_onboarding(
    data: schemas.OnboardingRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.name is not None:
        user.name = data.name
    if data.date_of_birth is not None:
        user.date_of_birth = datetime.fromisoformat(data.date_of_birth).date()
    if data.native_language is not None:
        user.native_language = data.native_language
    if data.occupation is not None:
        user.occupation = data.occupation
    if data.education_level is not None:
        user.education_level = data.education_level
    if data.current_band is not None:
        user.current_band = data.current_band
    if data.target_band is not None:
        user.target_band = data.target_band
    if data.exam_date is not None:
        user.exam_date = datetime.fromisoformat(data.exam_date).date()
    if data.ielts_module is not None:
        user.ielts_module = data.ielts_module
    if data.reason_for_ielts is not None:
        user.reason_for_ielts = data.reason_for_ielts
    if data.focus_skills is not None:
        user.focus_skills = data.focus_skills
    if data.study_hours_per_day is not None:
        user.study_hours_per_day = data.study_hours_per_day
    if data.daily_goal is not None:
        user.daily_goal = data.daily_goal

    user.onboarding_completed = True
    await db.commit()
    await db.refresh(user)

    plan = await service.generate_personalized_plan(user)
    return schemas.OnboardingResponse(success=True, plan=plan)


@router.post("/onboarding/skip")
async def skip_onboarding(
    data: schemas.OnboardingRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    user = await repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.name is not None:
        user.name = data.name
    if data.date_of_birth is not None:
        user.date_of_birth = datetime.fromisoformat(data.date_of_birth).date()
    if data.native_language is not None:
        user.native_language = data.native_language
    if data.occupation is not None:
        user.occupation = data.occupation
    if data.education_level is not None:
        user.education_level = data.education_level
    if data.current_band is not None:
        user.current_band = data.current_band
    if data.target_band is not None:
        user.target_band = data.target_band
    if data.exam_date is not None:
        user.exam_date = datetime.fromisoformat(data.exam_date).date()
    if data.ielts_module is not None:
        user.ielts_module = data.ielts_module
    if data.reason_for_ielts is not None:
        user.reason_for_ielts = data.reason_for_ielts
    if data.focus_skills is not None:
        user.focus_skills = data.focus_skills
    if data.study_hours_per_day is not None:
        user.study_hours_per_day = data.study_hours_per_day
    if data.daily_goal is not None:
        user.daily_goal = data.daily_goal

    await db.commit()
    return {"success": True, "skipped": True}
