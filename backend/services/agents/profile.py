from datetime import date
from typing import Optional
from services.agents.base import BaseAgent
from services.agents.registry import registry
from services.profile.schemas import PersonalizedPlan

@registry.register
class ProfileAgent(BaseAgent):
    name = "ProfileAgent"
    description = "Analyzes user profiles and generates personalized IELTS study plans."

    async def generate_personalized_plan(self, user) -> PersonalizedPlan:
        days_until_exam = None
        if user.exam_date:
            days_until_exam = (user.exam_date - date.today()).days

        focus = ", ".join(user.focus_skills) if getattr(user, 'focus_skills', None) else "all skills"
        module = getattr(user, 'ielts_module', "academic")
        reason = getattr(user, 'reason_for_ielts', "general improvement")

        prompt = f"""You are an expert IELTS tutor creating a personalized study plan.

Student Profile:
- Name: {user.name}
- Native Language: {getattr(user, 'native_language', "Not specified")}
- Occupation: {getattr(user, 'occupation', "Not specified")}
- Education: {getattr(user, 'education_level', "Not specified")}
- Current Band: {float(user.current_band)}
- Target Band: {float(user.target_band)}
- IELTS Module: {module}
- Reason for IELTS: {reason}
- Focus Skills: {focus}
- Study Hours Per Day: {getattr(user, 'study_hours_per_day', 2)}
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
            return await self.run_structured(
                prompt=prompt,
                schema=PersonalizedPlan,
                temperature=0.4
            )
        except Exception:
            # Fallback in case LLM fails
            return PersonalizedPlan(
                weekly_focus=[
                    "Week 1: Assess baseline & build study habits",
                    "Week 2: Focus on weakest skill area",
                    "Week 3: Vocabulary expansion & grammar patterns",
                    "Week 4: Timed practice & test strategies",
                ],
                skill_priorities=[
                    {"skill": s, "reason": "Selected as focus area", "suggested_hours": 1}
                    for s in (getattr(user, 'focus_skills', None) or ["reading", "writing", "listening", "speaking"])
                ],
                study_schedule_suggestion=(
                    f"With {getattr(user, 'study_hours_per_day', 2)} hours daily, split your time across "
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
