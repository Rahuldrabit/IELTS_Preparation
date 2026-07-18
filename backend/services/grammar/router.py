"""Grammar Service API router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import GrammarSkill, GrammarMistake, GrammarExercise, GrammarAttempt, GrammarNote, GrammarLearningHistory
from services.grammar.service import GrammarService
from services.grammar.exercise_engine import get_exercise_generator
from services.grammar.schemas import (
    DashboardResponse, JourneyMapResponse, LessonContentResponse,
    AIExplanationRequest, GrammarErrorAnalysisRequest, GrammarErrorAnalysisResponse,
    ExerciseGenerationRequest, ExerciseData, ExerciseSubmission, ExerciseEvaluationResponse,
    WritingPracticeRequest, WritingPracticeResponse, SpeakingFeedback,
    GrammarNoteSchema, KnowledgeGraphResponse, AnalyticsResponse,
    RecommendationsResponse, RecordMistakeRequest
)


router = APIRouter(prefix="/grammar", tags=["Grammar"])


def get_grammar_service() -> GrammarService:
    """Get grammar service instance."""
    return GrammarService()


# ============ Dashboard & Navigation ============

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user_id: int = 1,  # MVP: hardcoded user
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Get grammar dashboard data."""
    try:
        return await service.get_dashboard(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journey", response_model=JourneyMapResponse)
async def get_journey_map(
    service: GrammarService = Depends(get_grammar_service)
):
    """Get the full grammar journey map."""
    try:
        return await service.get_journey_map()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/{topic_id}/lesson", response_model=LessonContentResponse)
async def get_lesson_content(
    topic_id: int,
    service: GrammarService = Depends(get_grammar_service)
):
    """Get lesson content for a topic."""
    try:
        content = await service.get_lesson_content(topic_id)
        if not content:
            raise HTTPException(status_code=404, detail="Topic not found")
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ AI Explanation & Error Analysis ============

@router.post("/topics/{topic_id}/explain")
async def get_ai_explanation(
    topic_id: int,
    request: AIExplanationRequest,
    service: GrammarService = Depends(get_grammar_service)
):
    """Get AI-generated explanation for a topic at specified level/language."""
    try:
        explanation = await service.get_ai_explanation(
            topic_id, request.level, request.language
        )
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-error", response_model=GrammarErrorAnalysisResponse)
async def analyze_grammar_error(
    request: GrammarErrorAnalysisRequest,
    service: GrammarService = Depends(get_grammar_service)
):
    """Analyze a grammar error in a sentence."""
    try:
        return await service.analyze_grammar_error(request.sentence, request.context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Interactive Exercises ============

@router.post("/topics/{topic_id}/generate-exercises")
async def generate_exercises(
    topic_id: int,
    request: ExerciseGenerationRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Generate grammar exercises for a topic using AI."""
    from services.grammar.curriculum_loader import get_curriculum_loader
    from datetime import datetime
    
    try:
        loader = get_curriculum_loader()
        topic = loader.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
        
        # Get user's recent mistakes for this topic
        skill_result = await db.execute(
            select(GrammarSkill)
            .where(GrammarSkill.user_id == user_id)
            .where(GrammarSkill.skill_name == topic["topic_name"])
        )
        skill = skill_result.scalar_one_or_none()
        
        recent_mistakes = []
        if skill:
            mistakes_result = await db.execute(
                select(GrammarMistake)
                .where(GrammarMistake.skill_id == skill.id)
                .order_by(GrammarMistake.created_at.desc())
                .limit(5)
            )
            recent_mistakes = [
                {"incorrect": m.incorrect_sentence, "correct": m.correct_sentence}
                for m in mistakes_result.scalars().all()
            ]
        
        # Generate exercises using AI engine
        engine = get_exercise_generator()
        raw_exercises = await engine.generate_exercises(
            topic_name=topic["topic_name"],
            types=request.types,
            count=request.count,
            difficulty=request.difficulty,
            mistakes=recent_mistakes if recent_mistakes else None
        )
        
        # Persist exercises to DB and return with IDs
        result_exercises = []
        for ex_data in raw_exercises:
            exercise = GrammarExercise(
                topic_id=topic_id,
                exercise_type=ex_data["exercise_type"],
                question_data=ex_data["question_data"],
                correct_answer=ex_data["correct_answer"],
                explanation=ex_data.get("explanation", ""),
                difficulty=ex_data.get("difficulty", request.difficulty),
                generated_at=datetime.utcnow()
            )
            db.add(exercise)
            await db.flush()  # Get the ID
            
            result_exercises.append({
                "id": exercise.id,
                "exercise_type": exercise.exercise_type,
                "question_data": exercise.question_data,
                "correct_answer": exercise.correct_answer,
                "explanation": exercise.explanation,
                "difficulty": exercise.difficulty
            })
        
        await db.commit()
        return result_exercises
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exercises/evaluate")
async def evaluate_exercise(
    submission: ExerciseSubmission,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Evaluate a user's exercise answer using AI."""
    from datetime import datetime
    
    try:
        # Get the exercise
        result = await db.execute(
            select(GrammarExercise).where(GrammarExercise.id == submission.exercise_id)
        )
        exercise = result.scalar_one_or_none()
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        # Evaluate using AI engine
        engine = get_exercise_generator()
        eval_result = await engine.evaluate_answer(
            exercise_type=exercise.exercise_type,
            question_data=exercise.question_data,
            correct_answer=exercise.correct_answer,
            user_answer=submission.user_answer
        )
        
        # Get or create skill for this topic
        from services.grammar.curriculum_loader import get_curriculum_loader
        loader = get_curriculum_loader()
        topic = loader.get_topic(exercise.topic_id)
        
        skill = None
        if topic:
            skill_result = await db.execute(
                select(GrammarSkill)
                .where(GrammarSkill.user_id == user_id)
                .where(GrammarSkill.skill_name == topic["topic_name"])
            )
            skill = skill_result.scalar_one_or_none()
        
        mastery_change = 0
        if skill:
            # Record attempt
            attempt = GrammarAttempt(
                user_id=user_id,
                exercise_id=exercise.id,
                skill_id=skill.id,
                user_answer=submission.user_answer,
                is_correct=eval_result["is_correct"],
                feedback=eval_result.get("feedback", ""),
                created_at=datetime.utcnow()
            )
            db.add(attempt)
            
            # Update mastery
            if eval_result["is_correct"]:
                skill.mastery = min(100, skill.mastery + 2)
                mastery_change = 2
            else:
                skill.mastery = max(0, skill.mastery - 1)
                mastery_change = -1
            
            skill.last_practiced = datetime.utcnow()
            
            # Record learning history
            history = GrammarLearningHistory(
                user_id=user_id,
                skill_id=skill.id,
                activity_type="exercise",
                details={"exercise_id": exercise.id, "is_correct": eval_result["is_correct"]},
                score=100 if eval_result["is_correct"] else 0,
                created_at=datetime.utcnow()
            )
            db.add(history)
            
            await db.commit()
        
        return {
            "is_correct": eval_result["is_correct"],
            "feedback": eval_result.get("feedback", ""),
            "correct_answer": exercise.correct_answer,
            "explanation": eval_result.get("explanation", exercise.explanation or ""),
            "mastery_change": mastery_change
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Writing & Speaking Practice ============

@router.post("/topics/{topic_id}/writing-practice", response_model=WritingPracticeResponse)
async def practice_writing(
    topic_id: int,
    request: WritingPracticeRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Evaluate grammar in written sentences."""
    try:
        return await service.practice_writing(topic_id, request, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topics/{topic_id}/speaking-practice")
async def practice_speaking(
    topic_id: int,
    audio: UploadFile = File(...),
    target_grammar: Optional[str] = Form(None),
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Evaluate grammar in spoken audio."""
    try:
        # Note: This endpoint needs audio transcription capability
        # For now, return placeholder response
        raise HTTPException(
            status_code=501,
            detail="Speaking practice endpoint requires audio transcription setup"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Grammar Notes & Mistake Tracking ============

@router.post("/skills/{skill_id}/record-mistake")
async def record_mistake(
    skill_id: int,
    request: RecordMistakeRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Record a grammar mistake."""
    try:
        return await service.record_mistake(skill_id, request, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes", response_model=List[GrammarNoteSchema])
async def get_grammar_notes(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Get user's grammar notes."""
    try:
        return await service.get_grammar_notes(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}")
async def dismiss_note(
    note_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """Dismiss a grammar note."""
    from shared.models import GrammarNote
    try:
        result = await db.execute(
            select(GrammarNote)
            .where(GrammarNote.id == note_id)
            .where(GrammarNote.user_id == user_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        note.is_dismissed = True
        await db.commit()
        
        return {"status": "dismissed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Knowledge Graph & Analytics ============

@router.get("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Get the grammar knowledge graph with user mastery."""
    try:
        return await service.get_knowledge_graph(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Get grammar analytics."""
    try:
        return await service.get_analytics(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Recommendations & Missions ============

@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Get AI-powered learning recommendations."""
    try:
        return await service.get_recommendations(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-daily-mission")
async def generate_daily_mission(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Generate daily grammar mission."""
    try:
        return await service.generate_daily_mission(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Existing endpoints for backward compatibility ============

@router.get("/topics")
async def get_topics_compatibility(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    service: GrammarService = Depends(get_grammar_service)
):
    """Get all grammar topics (backward compatibility)."""
    try:
        skills = await service.get_all_skills(user_id, db)
        return [
            {
                "id": skill.id,
                "skill_name": skill.skill_name,
                "description": skill.description,
                "mastery": skill.mastery,
                "mistake_count": skill.mistake_count,
                "last_practiced": skill.last_practiced.isoformat() if skill.last_practiced else None
            }
            for skill in skills
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))