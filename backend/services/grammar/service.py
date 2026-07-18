"""Business logic for Grammar Service."""
import asyncio
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from shared.models import (
    GrammarSkill, GrammarMistake, GrammarTopic, GrammarExercise,
    GrammarAttempt, GrammarNote, GrammarLearningHistory, DailyTask
)
from services.grammar.curriculum_loader import get_curriculum_loader
from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError
from services.grammar.schemas import (
    DashboardResponse, JourneyMapResponse, LessonContentResponse,
    GrammarErrorAnalysisResponse, ExerciseGenerationRequest,
    WritingPracticeRequest, WritingPracticeResponse, SpeakingFeedback,
    GrammarNoteSchema, KnowledgeGraphResponse, AnalyticsResponse,
    RecommendationsResponse, RecordMistakeRequest, ExerciseData,
    ExerciseEvaluationResponse, ExerciseSubmission
)


class GrammarService:
    """Service layer for grammar operations."""
    
    def __init__(self):
        self.curriculum_loader = get_curriculum_loader()
        self.ai_client = get_gemma_client()
    
    async def get_dashboard(self, user_id: int, db: AsyncSession) -> DashboardResponse:
        """Get grammar dashboard data."""
        # Get all grammar skills for the user
        result = await db.execute(
            select(GrammarSkill)
            .where(GrammarSkill.user_id == user_id)
            .order_by(GrammarSkill.mastery)
        )
        skills = result.scalars().all()
        
        if not skills:
            # Initialize skills from curriculum if none exist
            await self._initialize_user_skills(user_id, db)
            skills = await self.get_all_skills(user_id, db)
        
        # Calculate overall mastery
        total_mastery = sum(skill.mastery for skill in skills)
        overall_mastery = total_mastery / len(skills) if skills else 0
        
        # Find weakest and strongest topics
        weakest_topic = min(skills, key=lambda s: s.mastery, default=None)
        strongest_topic = max(skills, key=lambda s: s.mastery, default=None)
        
        # Get weak topics (mastery < 50)
        weak_topics = [skill for skill in skills if skill.mastery < 50]
        strong_topics = [skill for skill in skills if skill.mastery >= 70]
        
        # Get today's grammar-related daily tasks
        today = date.today()
        daily_tasks_result = await db.execute(
            select(DailyTask)
            .where(DailyTask.user_id == user_id)
            .where(DailyTask.date == today)
            .where(DailyTask.skill == "grammar")
            .where(DailyTask.completed == False)
        )
        daily_mission = daily_tasks_result.scalars().first()
        
        # Get continue learning (last practiced topic)
        continue_learning = None
        last_practiced = max(skills, key=lambda s: s.last_practiced or datetime.min, default=None)
        if last_practiced and last_practiced.last_practiced:
            continue_learning = {
                "skill_id": last_practiced.id,
                "skill_name": last_practiced.skill_name,
                "last_practiced": last_practiced.last_practiced
            }
        
        # Calculate today's accuracy (simplified)
        today_start = datetime.combine(today, datetime.min.time())
        attempts_result = await db.execute(
            select(GrammarAttempt)
            .where(GrammarAttempt.user_id == user_id)
            .where(GrammarAttempt.created_at >= today_start)
        )
        today_attempts = attempts_result.scalars().all()
        
        today_accuracy = None
        if today_attempts:
            correct_count = sum(1 for attempt in today_attempts if attempt.is_correct)
            today_accuracy = (correct_count / len(today_attempts)) * 100
        
        # Calculate grammar streak (consecutive days with grammar practice)
        grammar_streak = await self._calculate_grammar_streak(user_id, db)
        
        return DashboardResponse(
            overall_mastery=overall_mastery,
            today_accuracy=today_accuracy,
            grammar_streak=grammar_streak,
            weakest_topic=weakest_topic,
            strongest_topic=strongest_topic,
            daily_mission=daily_mission,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            continue_learning=continue_learning
        )
    
    async def get_journey_map(self) -> JourneyMapResponse:
        """Get the full grammar journey map."""
        return JourneyMapResponse(**self.curriculum_loader.get_journey_map())
    
    async def get_lesson_content(self, topic_id: int) -> Optional[LessonContentResponse]:
        """Get lesson content for a topic."""
        lesson_data = self.curriculum_loader.get_lesson_content(topic_id)
        if not lesson_data:
            return None
        
        return LessonContentResponse(**lesson_data)
    
    async def get_ai_explanation(
        self, topic_id: int, level: str, language: str
    ) -> str:
        """Get AI-generated explanation for a topic."""
        topic = self.curriculum_loader.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        # Build prompt for AI explanation
        prompt = f"""Provide a {level}-level explanation of '{topic['topic_name']}' in {language}.
        
        Rules to explain:
        {chr(10).join([f"- {rule.get('rule', '')}" for rule in topic.get('rules', [])])}
        
        Examples:
        {chr(10).join([f"- {example}" for example in topic.get('examples', {}).get('medium', [])])}
        
        Explain the concept clearly at a {level} level, focusing on practical usage for IELTS preparation."""
        
        try:
            explanation = await asyncio.to_thread(
                self.ai_client.generate_text,
                prompt=prompt,
                system_prompt=f"You are an IELTS grammar tutor explaining {topic['topic_name']}.",
                temperature=0.7
            )
            return explanation
        except GemmaClientError:
            return f"Explanation unavailable. Please try again later."
    
    async def analyze_grammar_error(
        self, sentence: str, context: Optional[str] = None
    ) -> GrammarErrorAnalysisResponse:
        """Analyze a grammar error in a sentence."""
        prompt = f"""Analyze this sentence for grammar errors: "{sentence}"
        
        {f"Context: {context}" if context else ""}
        
        Classify the error using IELTS grammar taxonomy:
        - Articles (a, an, the, zero article)
        - Tenses (present, past, future, perfect, continuous)
        - Subject-Verb Agreement
        - Pronouns (personal, relative, demonstrative, possessive, reflexive)
        - Relative Clauses
        - Passive Voice
        - Conditionals
        - Word Order
        - Connectors (although, however, despite, whereas, etc.)
        - Prepositions
        - Punctuation
        - Parallelism
        - Modifiers
        - Cohesion
        
        Provide the error category, specific error type, explanation, correct sentence,
        and 2-3 alternative expressions.
        
        Return JSON format matching GrammarErrorAnalysisResponse schema."""
        
        try:
            response = await asyncio.to_thread(
                self.ai_client.generate_structured,
                prompt=prompt,
                schema=GrammarErrorAnalysisResponse,
                temperature=0.3
            )
            return response
        except GemmaClientError:
            # Fallback analysis
            return GrammarErrorAnalysisResponse(
                category="Unknown",
                error_type="Analysis unavailable",
                explanation="AI analysis service is temporarily unavailable.",
                correct_sentence=sentence,
                alternative_expressions=[],
                practice_recommendation="Try again later or consult grammar reference materials."
            )
    
    async def generate_exercises(
        self, topic_id: int, request: ExerciseGenerationRequest, user_id: int, db: AsyncSession
    ) -> List[ExerciseData]:
        """Generate grammar exercises for a topic."""
        topic = self.curriculum_loader.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        # Get user's recent mistakes for this topic
        skill = await self._get_or_create_skill(topic['topic_name'], user_id, db)
        if skill:
            mistakes_result = await db.execute(
                select(GrammarMistake)
                .where(GrammarMistake.skill_id == skill.id)
                .order_by(GrammarMistake.created_at.desc())
                .limit(5)
            )
            recent_mistakes = mistakes_result.scalars().all()
        else:
            recent_mistakes = []
        
        # Build prompt for exercise generation
        mistakes_context = ""
        if recent_mistakes:
            mistakes_list = "\n".join([
                f"- Incorrect: {m.incorrect_sentence} → Correct: {m.correct_sentence}"
                for m in recent_mistakes[:3]
            ])
            mistakes_context = f"\nUser's recent mistakes:\n{mistakes_list}"
        
        prompt = f"""Generate {request.count} grammar exercises for the topic: '{topic['topic_name']}'.
        
        Topic description: {topic.get('description', '')}
        
        Exercise types to include: {', '.join(request.types)}
        Difficulty level: {request.difficulty}
        {mistakes_context}
        
        For each exercise, provide:
        1. The question/activity
        2. The correct answer
        3. A brief explanation
        
        Return JSON array of exercises matching the ExerciseData schema."""
        
        try:
            # This would call the AI to generate exercises
            # For now, return placeholder
            exercises = []
            for i in range(request.count):
                exercise = GrammarExercise(
                    topic_id=topic_id,
                    exercise_type=request.types[i % len(request.types)],
                    question_data={"question": f"Sample question {i+1} for {topic['topic_name']}"},
                    correct_answer=f"Sample correct answer {i+1}",
                    explanation=f"Sample explanation {i+1}",
                    difficulty=request.difficulty,
                    generated_at=datetime.utcnow()
                )
                db.add(exercise)
                exercises.append(exercise)
            
            await db.commit()
            
            return [
                ExerciseData(
                    id=ex.id,
                    exercise_type=ex.exercise_type,
                    question_data=ex.question_data,
                    correct_answer=ex.correct_answer,
                    explanation=ex.explanation,
                    difficulty=ex.difficulty
                )
                for ex in exercises
            ]
        except Exception:
            # Return minimal exercises as fallback
            return []
    
    async def evaluate_exercise(
        self, exercise_id: int, user_answer: str, user_id: int, db: AsyncSession
    ) -> ExerciseEvaluationResponse:
        """Evaluate a user's exercise answer."""
        # Get the exercise
        result = await db.execute(
            select(GrammarExercise).where(GrammarExercise.id == exercise_id)
        )
        exercise = result.scalar_one_or_none()
        
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")
        
        # Get or create the grammar skill
        topic = self.curriculum_loader.get_topic(exercise.topic_id)
        if not topic:
            raise ValueError(f"Topic for exercise {exercise_id} not found")
        
        skill = await self._get_or_create_skill(topic['topic_name'], user_id, db)
        
        # Simple evaluation - in reality would use AI
        is_correct = user_answer.strip().lower() == exercise.correct_answer.strip().lower()
        
        # Record the attempt
        attempt = GrammarAttempt(
            user_id=user_id,
            exercise_id=exercise_id,
            skill_id=skill.id,
            user_answer=user_answer,
            is_correct=is_correct,
            feedback="Auto-evaluated" if is_correct else "Incorrect",
            created_at=datetime.utcnow()
        )
        db.add(attempt)
        
        # Update skill mastery
        if is_correct:
            skill.mastery = min(100, skill.mastery + 2)
            skill.confidence = min(1.0, skill.confidence + 0.05)
        else:
            skill.mastery = max(0, skill.mastery - 1)
            skill.confidence = max(0.0, skill.confidence - 0.02)
        
        skill.last_practiced = datetime.utcnow()
        
        # Record learning history
        history = GrammarLearningHistory(
            user_id=user_id,
            skill_id=skill.id,
            activity_type="exercise",
            details={"exercise_id": exercise_id, "is_correct": is_correct},
            score=100 if is_correct else 0,
            created_at=datetime.utcnow()
        )
        db.add(history)
        
        await db.commit()
        
        return ExerciseEvaluationResponse(
            is_correct=is_correct,
            feedback="Correct!" if is_correct else f"Incorrect. The correct answer is: {exercise.correct_answer}",
            correct_answer=exercise.correct_answer,
            explanation=exercise.explanation,
            mastery_change=2 if is_correct else -1
        )
    
    async def practice_writing(
        self, topic_id: int, request: WritingPracticeRequest, user_id: int, db: AsyncSession
    ) -> WritingPracticeResponse:
        """Evaluate grammar in written sentences."""
        topic = self.curriculum_loader.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        skill = await self._get_or_create_skill(topic['topic_name'], user_id, db)
        
        # Evaluate each sentence
        sentences_feedback = []
        correct_count = 0
        
        for sentence in request.sentences:
            # Analyze the sentence for grammar errors
            analysis = await self.analyze_grammar_error(sentence)
            
            # Check if target grammar structure is used
            target_structure_used = (
                request.target_grammar.lower() in analysis.category.lower()
                if request.target_grammar else True
            )
            
            is_correct = analysis.category == "Unknown" or not analysis.error_type
            
            if is_correct:
                correct_count += 1
            
            feedback = SentenceFeedback(
                sentence=sentence,
                is_correct=is_correct,
                grammar_feedback=analysis.explanation,
                target_structure_used=target_structure_used,
                estimated_band=6.5 if is_correct else 5.5
            )
            sentences_feedback.append(feedback)
        
        # Update mastery based on performance
        accuracy = (correct_count / len(request.sentences)) if request.sentences else 0
        
        if accuracy > 0.7:
            skill.mastery = min(100, skill.mastery + 3)
        elif accuracy > 0.4:
            skill.mastery = min(100, skill.mastery + 1)
        else:
            skill.mastery = max(0, skill.mastery - 1)
        
        skill.last_practiced = datetime.utcnow()
        
        # Record learning history
        history = GrammarLearningHistory(
            user_id=user_id,
            skill_id=skill.id,
            activity_type="writing_practice",
            details={
                "topic_id": topic_id,
                "sentence_count": len(request.sentences),
                "accuracy": accuracy
            },
            score=accuracy * 100,
            created_at=datetime.utcnow()
        )
        db.add(history)
        
        await db.commit()
        
        recommendations = []
        if accuracy < 0.5:
            recommendations.append(f"Review {topic['topic_name']} rules and examples.")
        if not all(fb.target_structure_used for fb in sentences_feedback):
            recommendations.append(f"Practice using {request.target_grammar or 'target grammar'} structures.")
        
        return WritingPracticeResponse(
            overall_accuracy=accuracy,
            sentences_feedback=sentences_feedback,
            recommendations=recommendations
        )
    
    async def record_mistake(
        self, skill_id: int, request: RecordMistakeRequest, user_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Record a grammar mistake."""
        # Get the skill
        result = await db.execute(
            select(GrammarSkill)
            .where(GrammarSkill.id == skill_id)
            .where(GrammarSkill.user_id == user_id)
        )
        skill = result.scalar_one_or_none()
        
        if not skill:
            raise ValueError(f"Skill {skill_id} not found for user {user_id}")
        
        # Record the mistake
        mistake = GrammarMistake(
            skill_id=skill_id,
            incorrect_sentence=request.incorrect_sentence,
            correct_sentence=request.correct_sentence,
            explanation=request.explanation,
            source=request.source,
            error_type=request.error_type,
            created_at=datetime.utcnow()
        )
        db.add(mistake)
        
        # Update skill stats
        skill.mistake_count += 1
        skill.mastery = max(0, skill.mastery - 2)
        skill.last_practiced = datetime.utcnow()
        
        # Update recent performance
        recent_perf = skill.recent_performance or {"scores": [], "timestamps": []}
        recent_perf["scores"].append(0)  # 0 for mistake
        recent_perf["timestamps"].append(datetime.utcnow().isoformat())
        
        # Keep only last 5 entries
        if len(recent_perf["scores"]) > 5:
            recent_perf["scores"] = recent_perf["scores"][-5:]
            recent_perf["timestamps"] = recent_perf["timestamps"][-5:]
        
        skill.recent_performance = recent_perf
        
        # Check if we should generate a grammar note (3 mistakes in same category)
        mistakes_result = await db.execute(
            select(GrammarMistake)
            .where(GrammarMistake.skill_id == skill_id)
            .where(GrammarMistake.error_type == request.error_type)
        )
        similar_mistakes = mistakes_result.scalars().all()
        
        if len(similar_mistakes) >= 3:
            # Generate grammar note
            note = GrammarNote(
                user_id=user_id,
                skill_id=skill_id,
                title=f"Common mistake: {request.error_type or 'Grammar Error'}",
                content=f"You've made this mistake {len(similar_mistakes)} times:\n\nIncorrect: {request.incorrect_sentence}\nCorrect: {request.correct_sentence}\n\nRemember: {request.explanation}",
                mistake_pattern=request.incorrect_sentence,
                correction=request.correct_sentence,
                example=f"Example: {request.correct_sentence}",
                created_at=datetime.utcnow()
            )
            db.add(note)
        
        await db.commit()
        
        return {"status": "recorded", "mistake_id": mistake.id}
    
    async def get_grammar_notes(self, user_id: int, db: AsyncSession) -> List[GrammarNoteSchema]:
        """Get user's grammar notes."""
        result = await db.execute(
            select(GrammarNote)
            .where(GrammarNote.user_id == user_id)
            .where(GrammarNote.is_dismissed == False)
            .order_by(GrammarNote.created_at.desc())
        )
        notes = result.scalars().all()
        
        return [GrammarNoteSchema.from_orm(note) for note in notes]
    
    async def get_knowledge_graph(self, user_id: int, db: AsyncSession) -> KnowledgeGraphResponse:
        """Get the grammar knowledge graph with user mastery."""
        # Get all curriculum topics
        all_topics = self.curriculum_loader.get_all_topics()
        
        # Get user's skills
        result = await db.execute(
            select(GrammarSkill).where(GrammarSkill.user_id == user_id)
        )
        user_skills = {skill.skill_name: skill for skill in result.scalars().all()}
        
        nodes = []
        for topic in all_topics:
            skill = user_skills.get(topic["topic_name"])
            
            node = KnowledgeGraphNode(
                topic_id=topic["topic_id"],
                topic_name=topic["topic_name"],
                module=topic["module_name"],
                mastery=skill.mastery if skill else 0,
                confidence=skill.confidence if skill else 0.0,
                recent_performance=skill.recent_performance.get("scores", []) if skill and skill.recent_performance else None,
                last_reviewed=skill.last_reviewed if skill else None,
                prerequisites=topic.get("prerequisites", [])
            )
            nodes.append(node)
        
        # Create edges based on prerequisites
        edges = []
        for node in nodes:
            for prereq_id in node.prerequisites:
                edges.append({
                    "from": prereq_id,
                    "to": node.topic_id,
                    "type": "prerequisite"
                })
        
        return KnowledgeGraphResponse(nodes=nodes, edges=edges)
    
    async def get_analytics(self, user_id: int, db: AsyncSession) -> AnalyticsResponse:
        """Get grammar analytics."""
        dashboard = await self.get_dashboard(user_id, db)
        
        # Get total exercises completed
        result = await db.execute(
            select(func.count(GrammarAttempt.id))
            .where(GrammarAttempt.user_id == user_id)
        )
        total_exercises = result.scalar() or 0
        
        # Calculate weekly improvement (simplified)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        result = await db.execute(
            select(GrammarAttempt)
            .where(GrammarAttempt.user_id == user_id)
            .where(GrammarAttempt.created_at >= week_ago)
        )
        recent_attempts = result.scalars().all()
        
        weekly_accuracy = 0.0
        if recent_attempts:
            correct_count = sum(1 for attempt in recent_attempts if attempt.is_correct)
            weekly_accuracy = (correct_count / len(recent_attempts)) * 100
        
        return AnalyticsResponse(
            overall_grammar=dashboard.overall_mastery,
            today_accuracy=dashboard.today_accuracy,
            grammar_streak=dashboard.grammar_streak,
            weakest_topic=dashboard.weakest_topic.skill_name if dashboard.weakest_topic else "N/A",
            strongest_topic=dashboard.strongest_topic.skill_name if dashboard.strongest_topic else "N/A",
            total_exercises_completed=total_exercises,
            weekly_improvement=weekly_accuracy,
            weekly_stats={
                "attempts_last_week": len(recent_attempts),
                "weekly_accuracy": weekly_accuracy
            }
        )
    
    async def get_recommendations(self, user_id: int, db: AsyncSession) -> RecommendationsResponse:
        """Get AI-powered learning recommendations."""
        # Get user's skills sorted by mastery
        result = await db.execute(
            select(GrammarSkill)
            .where(GrammarSkill.user_id == user_id)
            .order_by(GrammarSkill.mastery)
        )
        skills = result.scalars().all()
        
        if not skills:
            return RecommendationsResponse(recommendations=[], generated_at=datetime.utcnow())
        
        recommendations = []
        
        # Recommend weakest topics first
        for skill in skills[:3]:  # Top 3 weakest
            if skill.mastery < 50:
                topic = self.curriculum_loader.get_topic_by_name(skill.skill_name)
                if topic:
                    recommendations.append({
                        "topic_id": topic["topic_id"],
                        "topic_name": skill.skill_name,
                        "reason": f"Low mastery ({skill.mastery}%) - needs review",
                        "priority": "high",
                        "suggested_activities": [
                            "Review lesson content",
                            "Complete practice exercises",
                            "Try writing practice sentences"
                        ]
                    })
        
        # Recommend topics not practiced recently
        for skill in skills:
            if skill.last_practiced and (datetime.utcnow() - skill.last_practiced).days > 7:
                topic = self.curriculum_loader.get_topic_by_name(skill.skill_name)
                if topic and topic["topic_id"] not in [r["topic_id"] for r in recommendations]:
                    recommendations.append({
                        "topic_id": topic["topic_id"],
                        "topic_name": skill.skill_name,
                        "reason": f"Not practiced in {(datetime.utcnow() - skill.last_practiced).days} days",
                        "priority": "medium",
                        "suggested_activities": [
                            "Quick review",
                            "Refresh with examples"
                        ]
                    })
        
        # If no specific recommendations, suggest next topic in curriculum
        if not recommendations and skills:
            # Find highest mastered topic and suggest next in sequence
            highest_skill = max(skills, key=lambda s: s.mastery)
            topic = self.curriculum_loader.get_topic_by_name(highest_skill.skill_name)
            if topic:
                # Find next topic in same module
                module_topics = self.curriculum_loader.get_topics_by_module(topic["module_id"])
                current_index = next((i for i, t in enumerate(module_topics) if t["topic_id"] == topic["topic_id"]), -1)
                if current_index + 1 < len(module_topics):
                    next_topic = module_topics[current_index + 1]
                    recommendations.append({
                        "topic_id": next_topic["topic_id"],
                        "topic_name": next_topic["topic_name"],
                        "reason": "Next topic in learning sequence",
                        "priority": "medium",
                        "suggested_activities": [
                            "Start new lesson",
                            "Preview examples"
                        ]
                    })
        
        return RecommendationsResponse(
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
    
    async def generate_daily_mission(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Generate daily grammar mission."""
        recommendations = await self.get_recommendations(user_id, db)
        
        if not recommendations.recommendations:
            return {"message": "No recommendations available"}
        
        # Pick the highest priority recommendation
        priority_order = {"high": 3, "medium": 2, "low": 1}
        top_rec = max(
            recommendations.recommendations,
            key=lambda r: priority_order.get(r["priority"], 0)
        )
        
        # Create daily task
        today = date.today()
        mission = DailyTask(
            user_id=user_id,
            title=f"Practice {top_rec['topic_name']}",
            skill="grammar",
            completed=False,
            date=today,
            created_at=datetime.utcnow()
        )
        db.add(mission)
        await db.commit()
        
        return {
            "mission_created": True,
            "mission_id": mission.id,
            "topic": top_rec["topic_name"],
            "reason": top_rec["reason"],
            "suggested_activities": top_rec["suggested_activities"]
        }
    
    # ============ Helper Methods ============
    
    async def _initialize_user_skills(self, user_id: int, db: AsyncSession) -> None:
        """Initialize grammar skills for a new user from curriculum."""
        all_topics = self.curriculum_loader.get_all_topics()
        
        for topic in all_topics:
            skill = GrammarSkill(
                user_id=user_id,
                skill_name=topic["topic_name"],
                description=topic.get("description"),
                module=topic["module_name"],
                mastery=0,
                confidence=0.0,
                mistake_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(skill)
        
        await db.commit()
    
    async def _get_or_create_skill(self, skill_name: str, user_id: int, db: AsyncSession) -> GrammarSkill:
        """Get or create a grammar skill for a user."""
        result = await db.execute(
            select(GrammarSkill)
            .where(GrammarSkill.user_id == user_id)
            .where(GrammarSkill.skill_name == skill_name)
        )
        skill = result.scalar_one_or_none()
        
        if not skill:
            # Create new skill
            topic = self.curriculum_loader.get_topic_by_name(skill_name)
            skill = GrammarSkill(
                user_id=user_id,
                skill_name=skill_name,
                description=topic.get("description") if topic else None,
                module=topic["module_name"] if topic else "Unknown",
                mastery=0,
                confidence=0.0,
                mistake_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(skill)
            await db.commit()
            await db.refresh(skill)
        
        return skill
    
    async def _calculate_grammar_streak(self, user_id: int, db: AsyncSession) -> int:
        """Calculate consecutive days with grammar practice."""
        # Get all grammar learning history dates
        result = await db.execute(
            select(GrammarLearningHistory.created_at)
            .where(GrammarLearningHistory.user_id == user_id)
            .order_by(GrammarLearningHistory.created_at.desc())
        )
        history_dates = result.scalars().all()
        
        if not history_dates:
            return 0
        
        # Convert to dates
        dates_set = {h.date() for h in history_dates}
        dates_sorted = sorted(dates_set, reverse=True)
        
        # Calculate streak
        streak = 0
        current_date = date.today()
        
        for i, practice_date in enumerate(dates_sorted):
            if i == 0 and practice_date == current_date:
                streak = 1
            elif i == 0 and practice_date == current_date - timedelta(days=1):
                streak = 1  # Yesterday counts as start of streak
            elif i > 0 and practice_date == dates_sorted[i-1] - timedelta(days=1):
                streak += 1
            else:
                break
        
        return streak
    
    async def get_all_skills(self, user_id: int, db: AsyncSession) -> List[GrammarSkill]:
        """Get all grammar skills for a user."""
        result = await db.execute(
            select(GrammarSkill)
            .where(GrammarSkill.user_id == user_id)
            .order_by(GrammarSkill.mastery)
        )
        return result.scalars().all()