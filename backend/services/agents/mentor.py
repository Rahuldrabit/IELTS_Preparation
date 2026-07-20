from pydantic import BaseModel, Field
from typing import List, Optional
from services.agents.base import BaseAgent
from services.agents.registry import registry

class ChatResponse(BaseModel):
    response: str = Field(..., description="The mentor's response to the user")
    type: str = Field(default="message", description="Type of message: 'message', 'recommendation', 'hint'")

class DailyTask(BaseModel):
    title: str = Field(..., description="Task title")
    skill: str = Field(..., description="Target skill (e.g., reading, speaking)")
    priority: str = Field(..., description="Priority (high, medium, low)")

class DailyPlan(BaseModel):
    tasks: List[DailyTask] = Field(..., description="List of tasks for the day")

SYSTEM_PROMPTS = {
    "dashboard": "You are a friendly IELTS mentor. Keep responses under 50 words. Be encouraging.",
    "practice": "You are an IELTS tutor. Give specific, actionable advice on the current exercise.",
    "analytics": "You are a data-driven IELTS coach. Help the student understand their progress and focus on weak areas.",
    "profile": "You are a personal IELTS advisor. Help the student set realistic goals based on their current level.",
}

@registry.register
class MentorAgent(BaseAgent):
    name = "MentorAgent"
    description = "Provides general IELTS study advice, motivation, and daily planning."

    async def chat(self, message: str, page: str = "dashboard", context: Optional[str] = None) -> ChatResponse:
        system_prompt = SYSTEM_PROMPTS.get(page, SYSTEM_PROMPTS["dashboard"])
        
        prompt = system_prompt
        if context:
            prompt += f"\n\nUser Context: {context}"
        
        prompt += f"\n\nStudent message: {message}"
        
        # We can just return a basic string response and infer type.
        response = await self.run_text(prompt=prompt, temperature=0.7)
        
        msg_type = "message"
        if any(word in response.lower() for word in ["recommend", "suggest", "try"]):
            msg_type = "recommendation"
        elif any(word in response.lower() for word in ["tip", "remember", "note"]):
            msg_type = "hint"
            
        return ChatResponse(response=response, type=msg_type)
    
    async def get_mentor_message(self, page: str = "dashboard") -> str:
        system_prompt = SYSTEM_PROMPTS.get(page, SYSTEM_PROMPTS["dashboard"])
        prompt = f"{system_prompt}\nGive me a brief motivational message and one tip."
        
        return await self.run_text(prompt=prompt, temperature=0.7)

    async def generate_daily_plan(self) -> DailyPlan:
        prompt = "You are a study planner for IELTS preparation. Generate a daily study plan with 5 tasks."
        
        try:
            return await self.run_structured(
                prompt=prompt,
                schema=DailyPlan,
                temperature=0.7
            )
        except Exception:
            return DailyPlan(
                tasks=[
                    DailyTask(title="Complete 2 reading passages", skill="reading", priority="high"),
                    DailyTask(title="Practice 10 vocabulary words", skill="vocabulary", priority="medium"),
                    DailyTask(title="Listen to a podcast and take notes", skill="listening", priority="medium"),
                    DailyTask(title="Record a 2-minute speaking response", skill="speaking", priority="low"),
                    DailyTask(title="Write an essay and get AI feedback", skill="writing", priority="high"),
                ]
            )
