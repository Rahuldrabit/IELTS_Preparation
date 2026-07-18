"""Profile Service - User profile, band scores, milestones, daily roadmap."""
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import User, Milestone, DailyTask
from services.agents.syllabus import SyllabusCuratorAgent, SkillTelemetrySummary
from services.ai_agent.gemma_client import GemmaClientError


# ============ Router ============

router = APIRouter(prefix="/profile", tags=["Profile"])


# ============ Pydantic Schemas ============

class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    current_band: float
    target_band: float
    exam_date: Optional[str] = None
    daily_goal: int
    tasks_completed: int
    streak: int
    # Onboarding / Personalization
    onboarding_completed: bool
    native_language: Optional[str] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None  # high_school | bachelors | masters | phd
    ielts_module: Optional[str] = None  # academic | general
    reason_for_ielts: Optional[str] = None  # immigration | university | career | other
    focus_skills: Optional[list[str]] = None  # ["reading", "writing", "listening", "speaking"]
    study_hours_per_day: Optional[int] = None

    class Config:
        from_attributes = True


class BandScore(BaseModel):
    overall: float
    reading: float
    listening: float
    speaking: float
    writing: float


class MilestoneSchema(BaseModel):
    id: int
    band: float
    title: str
    description: str
    status: str
    skills: dict

    class Config:
        from_attributes = True


class DailyTaskSchema(BaseModel):
    id: int
    title: str
    skill: str
    completed: bool

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    tasks: list[DailyTaskSchema]
    completed_count: int
    total_count: int


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    target_band: Optional[float] = None
    exam_date: Optional[str] = None
    daily_goal: Optional[int] = None


# Feature preferences — mirrors the frontend FeatureConfig interface
DEFAULT_FEATURES = {
    "reading":   {"telemetry": False, "confidenceFlags": False},
    "writing":   {"scaffoldMode": False, "liveEvaluation": False},
    "listening": {"acousticLevel": 1,   "telemetry": False},
    "speaking":  {"mutationEngine": False, "workletRecorder": False},
}


class SkillFeaturesUpdate(BaseModel):
    """Partial skill features — any subset of keys is valid."""
    reading: Optional[dict] = None
    writing: Optional[dict] = None
    listening: Optional[dict] = None
    speaking: Optional[dict] = None


# ============ Endpoints ============

@router.get("", response_model=UserProfile)
async def get_profile(db: AsyncSession = Depends(get_db)):
    """Get the current user's profile."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
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


@router.put("", response_model=UserProfile)
async def update_profile(
    updates: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

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

    return UserProfile(
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
    )


@router.get("/band-scores", response_model=BandScore)
async def get_band_scores(db: AsyncSession = Depends(get_db)):
    """Get user's band scores across all skills."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current = float(user.current_band)
    return BandScore(
        overall=current,
        reading=current + 0.5,
        listening=current,
        speaking=current - 0.5,
        writing=current,
    )


@router.get("/milestones", response_model=list[MilestoneSchema])
async def get_milestones(db: AsyncSession = Depends(get_db)):
    """Get user's progress milestones."""
    result = await db.execute(
        select(Milestone).where(Milestone.user_id == 1).order_by(Milestone.band)
    )
    milestones = result.scalars().all()

    return [
        MilestoneSchema(
            id=m.id,
            band=float(m.band),
            title=m.title,
            description=m.description,
            status=m.status,
            skills=m.skills or {},
        )
        for m in milestones
    ]


@router.get("/roadmap", response_model=RoadmapResponse)
async def get_roadmap(db: AsyncSession = Depends(get_db)):
    """Get today's roadmap tasks. If none exist for today, re-date existing tasks."""
    today = date.today()
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.user_id == 1,
            DailyTask.date == today,
        )
    )
    tasks = result.scalars().all()

    # If no tasks for today, re-date all user tasks to today (daily reset)
    if not tasks:
        all_result = await db.execute(
            select(DailyTask).where(DailyTask.user_id == 1)
        )
        all_tasks = all_result.scalars().all()
        for t in all_tasks:
            t.date = today
            t.completed = False
        await db.commit()
        tasks = all_tasks

    return RoadmapResponse(
        tasks=[
            DailyTaskSchema(id=t.id, title=t.title, skill=t.skill, completed=t.completed)
            for t in tasks
        ],
        completed_count=sum(1 for t in tasks if t.completed),
        total_count=len(tasks),
    )


@router.patch("/roadmap/{task_id}/complete")
async def complete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a roadmap task as complete."""
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.id == task_id,
            DailyTask.user_id == 1,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = True
    await db.commit()

    # Increment user's tasks_completed
    user_result = await db.execute(select(User).where(User.id == 1))
    user = user_result.scalar_one()
    user.tasks_completed += 1

    # Check if all tasks are complete - update streak
    today = date.today()
    all_tasks_result = await db.execute(
        select(DailyTask).where(
            DailyTask.user_id == 1,
            DailyTask.date == today,
        )
    )
    all_tasks = all_tasks_result.scalars().all()
    if all(t.completed for t in all_tasks):
        user.streak += 1

    await db.commit()

    return {"status": "completed", "task_id": task_id}


# ─── Feature Preferences ────────────────────────────────────────────────────────

def _merge_features(stored: dict) -> dict:
    """Deep-merge stored features over DEFAULT_FEATURES, filling missing keys."""
    result = {}
    for skill, defaults in DEFAULT_FEATURES.items():
        result[skill] = {**defaults, **(stored.get(skill) or {})}
    return result


@router.get("/features")
async def get_features(db: AsyncSession = Depends(get_db)):
    """Return user's feature preferences, deep-merged over defaults."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _merge_features(user.features_config or {})


@router.patch("/features")
async def update_features(
    updates: SkillFeaturesUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Merge incoming skill feature updates into stored config. Returns full merged config."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = dict(user.features_config or {})
    payload = updates.model_dump(exclude_none=True)
    for skill, vals in payload.items():
        if vals:
            existing.setdefault(skill, {}).update(vals)

    user.features_config = existing
    await db.commit()
    return _merge_features(existing)


# ─── Autonomous Syllabus Curating Agent ─────────────────────────────────────────

@router.get("/uma-intervention")
async def get_uma_intervention(db: AsyncSession = Depends(get_db)):
    """
    Return the latest Uma intervention from the Autonomous Syllabus Curating Agent.
    Returns null if no analysis has been run yet (new user).
    """
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.ava_intervention or None


@router.post("/uma-intervention/refresh")
async def refresh_uma_intervention(
    telemetry: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the Autonomous Syllabus Curating Agent with fresh telemetry.
    Called automatically after each session submission (fire-and-forget from client).
    Stores the result in user.ava_intervention for dashboard display.
    """
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
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
                (user.exam_date - __import__("datetime").date.today()).days
                if user.exam_date else None
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


# ─── Journey Recommendation ─────────────────────────────────────────────────────


# Mapping from IELTS question type tags (used in ava_intervention) to generation params
_DIFFICULTY_MAP = {
    "TRUE_FALSE_NOT_GIVEN": "intermediate",
    "MATCHING_HEADINGS": "advanced",
    "SUMMARY_COMPLETION": "intermediate",
    "MULTIPLE_CHOICE": "intermediate",
    "SENTENCE_COMPLETION": "intermediate",
}


class JourneyRecommendation(BaseModel):
    """Recommended next practice session from the AI journey system."""
    skill: str               # reading | writing | listening | speaking
    topic: str               # e.g. "marine biology", "urban planning"
    difficulty: str          # beginner | intermediate | advanced
    question_type: str       # IELTS question type string
    reason: str              # Why this was recommended


@router.get("/journey-recommendation", response_model=JourneyRecommendation)
async def get_journey_recommendation(db: AsyncSession = Depends(get_db)):
    """
    Return the AI-recommended next skill and generation parameters.
    Uses ava_intervention if available, otherwise computes from user profile.
    """
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If the Syllabus Curator has run and we have an intervention, use it
    intervention = user.ava_intervention
    if intervention:
        skill = intervention.get("targeted_skill", "reading")
        topic = intervention.get("drill_topic", "general")
        question_type = intervention.get("drill_question_type", "MULTIPLE_CHOICE")
        difficulty = _DIFFICULTY_MAP.get(question_type, "intermediate")
        reason = intervention.get("insight_text", "Based on your recent performance analysis.")
        return JourneyRecommendation(
            skill=skill,
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            reason=reason,
        )

    # Fallback: use onboarding data
    focus_skills = user.focus_skills or []
    skill = focus_skills[0] if focus_skills else "reading"

    # Default topic and question type based on skill
    defaults = {
        "reading": ("technology", "TRUE_FALSE_NOT_GIVEN"),
        "writing": ("education", "TASK_2_ESSAY"),
        "listening": ("daily life", "FILL_BLANK"),
        "speaking": ("hobbies", "PART_2_CUE_CARD"),
    }
    topic, question_type = defaults.get(skill, ("general", "MULTIPLE_CHOICE"))

    return JourneyRecommendation(
        skill=skill,
        topic=topic,
        difficulty="intermediate",
        question_type=question_type,
        reason=f"Starting with {skill} based on your study preferences.",
    )


# ─── Onboarding ─────────────────────────────────────────────────────────────────


class OnboardingRequest(BaseModel):
    """Data collected during the onboarding wizard."""
    # Step 1: Personal Info
    name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO date string
    native_language: Optional[str] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None  # high_school, bachelors, masters, phd, other

    # Step 2: IELTS Goals
    current_band: Optional[float] = None
    target_band: Optional[float] = None
    exam_date: Optional[str] = None  # ISO date string
    ielts_module: Optional[str] = None  # academic | general
    reason_for_ielts: Optional[str] = None  # immigration, university, career, other

    # Step 3: Study Preferences
    focus_skills: Optional[list[str]] = None  # e.g. ["reading", "writing"]
    study_hours_per_day: Optional[int] = None
    daily_goal: Optional[int] = None


class PersonalizedPlan(BaseModel):
    """AI-generated personalized study plan returned after onboarding."""
    weekly_focus: list[str]
    skill_priorities: list[dict]  # [{skill, reason, suggested_hours}]
    study_schedule_suggestion: str
    motivational_message: str
    estimated_weeks_to_target: Optional[int] = None


class OnboardingResponse(BaseModel):
    """Response after completing onboarding."""
    success: bool
    plan: PersonalizedPlan


@router.get("/onboarding-status")
async def get_onboarding_status(db: AsyncSession = Depends(get_db)):
    """Check whether the current user has completed onboarding."""
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"completed": user.onboarding_completed}


@router.post("/onboarding", response_model=OnboardingResponse)
async def submit_onboarding(
    data: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Save onboarding data and generate a personalized AI study plan.
    Sets onboarding_completed = True on success.
    """
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ── Save onboarding fields ──────────────────────────────────────────────────
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

    # ── Generate personalized plan via AI ────────────────────────────────────────
    plan = await _generate_personalized_plan(user)

    return OnboardingResponse(success=True, plan=plan)


@router.post("/onboarding/skip")
async def skip_onboarding(
    data: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Partial save when user clicks 'Skip for now'.
    Saves whatever fields were filled but does NOT set onboarding_completed.
    """
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Save any fields that were provided
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


async def _generate_personalized_plan(user: User) -> PersonalizedPlan:
    """Use AI to generate a personalized IELTS study plan based on user profile."""
    from services.ai_agent.gemma_client import get_gemma_client

    # Build context for the AI
    days_until_exam = None
    if user.exam_date:
        days_until_exam = (user.exam_date - date.today()).days

    focus = ", ".join(user.focus_skills) if user.focus_skills else "all skills"
    module = user.ielts_module or "academic"
    reason = user.reason_for_ielts or "general improvement"

    prompt = f"""You are an expert IELTS tutor creating a personalized study plan.

Student Profile:
- Name: {user.name}
- Native Language: {user.native_language or "Not specified"}
- Occupation: {user.occupation or "Not specified"}
- Education: {user.education_level or "Not specified"}
- Current Band: {float(user.current_band)}
- Target Band: {float(user.target_band)}
- IELTS Module: {module}
- Reason for IELTS: {reason}
- Focus Skills: {focus}
- Study Hours Per Day: {user.study_hours_per_day or 2}
- Days Until Exam: {days_until_exam or "No deadline set"}

Create a personalized study plan. Consider:
1. Their native language interference patterns
2. Their occupation (relevant topics for writing/speaking)
3. The gap between current and target band
4. Time available before exam
5. Their preferred focus skills

Return a JSON object with:
- weekly_focus: list of 4-5 weekly theme strings (e.g. "Week 1: Foundation building - grammar patterns")
- skill_priorities: list of objects with "skill", "reason", "suggested_hours" keys
- study_schedule_suggestion: a 2-3 sentence daily schedule recommendation
- motivational_message: a warm, encouraging 2-sentence message personalized to their goal
- estimated_weeks_to_target: integer estimate of weeks needed (null if unsure)"""

    try:
        client = get_gemma_client()
        plan = client.generate_structured(
            prompt,
            schema=PersonalizedPlan,
            temperature=0.4,
        )
        return plan
    except GemmaClientError:
        # Fallback plan if AI is unavailable
        return PersonalizedPlan(
            weekly_focus=[
                "Week 1: Assess baseline & build study habits",
                "Week 2: Focus on weakest skill area",
                "Week 3: Vocabulary expansion & grammar patterns",
                "Week 4: Timed practice & test strategies",
            ],
            skill_priorities=[
                {"skill": s, "reason": "Selected as focus area", "suggested_hours": 1}
                for s in (user.focus_skills or ["reading", "writing", "listening", "speaking"])
            ],
            study_schedule_suggestion=(
                f"With {user.study_hours_per_day or 2} hours daily, split your time across "
                f"focused skill practice and review. Start each session with 10 minutes of "
                f"vocabulary review, then dedicate blocks to your priority skills."
            ),
            motivational_message=(
                f"Welcome, {user.name}! Your journey from band {float(user.current_band)} "
                f"to {float(user.target_band)} is absolutely achievable with consistent practice. "
                f"Let's build your skills step by step."
            ),
            estimated_weeks_to_target=None,
        )
