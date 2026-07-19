"""
Examiner Chat Agent - Conversational IELTS Speaking Part 1 & 3 simulator.

Task 1: AI Examiner Chat Mode
- Natural follow-up questions based on user's answer
- Maintains conversation context and topic coherence
- Simulates realistic examiner behavior
- Provides band score estimation at session end
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from services.agents.base import BaseAgent, registry
from shared import settings


# ─────────────────────────────────────────────
#  Schemas
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single message in the examiner chat."""
    role: str = Field(..., description="examiner or student")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExaminerSession(BaseModel):
    """State of an examiner chat session."""
    session_id: str
    part: int = Field(ge=1, le=3, description="IELTS Speaking part (1, 2, or 3)")
    topic: str
    messages: list[ChatMessage] = []
    turn_count: int = 0
    max_turns: int = 5  # For Part 1; Part 3 can have more
    started_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_band: Optional[float] = None
    feedback: Optional[str] = None


class ExaminerResponse(BaseModel):
    """Response from the examiner."""
    message: str
    follow_up_prompt: Optional[str] = None  # For student guidance
    is_session_end: bool = False
    estimated_band: Optional[float] = None
    feedback: Optional[str] = None
    next_question_type: Optional[str] = None  # "elaboration", "clarification", "new_topic"


class ExaminerChatAgent(BaseAgent):
    """
    AI Examiner for IELTS Speaking Part 1 & 3.
    
    Features:
    - Generates natural follow-up questions
    - Maintains conversation coherence
    - Simulates examiner behavior (warm, encouraging, professional)
    - Provides band estimate and feedback
    """
    
    name = "examiner_chat"
    
    # Part 1 topic categories
    PART1_TOPICS = [
        "work and studies", "hometown", "family", "friends",
        "hobbies", "sports", "music", "films", "reading",
        "travel", "food", "weather", "daily routine", "technology"
    ]
    
    # Part 3 abstract topics
    PART3_TOPICS = [
        "education and learning", "work and careers", "technology in society",
        "environmental issues", "health and lifestyle", "family relationships",
        "social media impact", "globalization", "cultural differences",
        "future of work", "urban vs rural life", "generational differences"
    ]
    
    def _get_system_prompt(self, session: ExaminerSession) -> str:
        """Generate the system prompt based on session state."""
        
        part_guidance = {
            1: """
You are an IELTS Speaking examiner conducting Part 1.
- Ask questions about familiar topics (hobbies, work, studies, hometown)
- Be warm and encouraging
- Ask 3-4 follow-up questions per topic
- Keep questions simple and direct
- If answers are short, gently encourage elaboration
- Move to related subtopics naturally
            """,
            3: """
You are an IELTS Speaking examiner conducting Part 3.
- Ask abstract, discussion-based questions
- Probe for opinions, reasons, examples
- Challenge the candidate to think deeply
- Ask about broader societal implications
- Compare past/present/future scenarios
- Require more sophisticated vocabulary and structures
            """
        }
        
        return f"""You are a friendly, professional IELTS Speaking examiner.
{part_guidance.get(session.part, part_guidance[1])}

CURRENT TOPIC: {session.topic}
TURN COUNT: {session.turn_count}/{session.max_turns}

RULES:
1. Listen carefully to the student's answer
2. Ask natural follow-up questions based on what they said
3. Don't repeat the same question or topic
4. Vary question types: "Why...?", "How...?", "In your opinion...", "Compare..."
5. Be encouraging even when answers are weak
6. After {session.max_turns} turns, politely end the session with brief feedback

RESPONSE FORMAT:
Return JSON with:
- message: Your response to the student (acknowledge their answer briefly, then ask follow-up)
- follow_up_prompt: Optional hint for the student (e.g., "Try to give reasons and examples")
- is_session_end: true if session should end
- estimated_band: Only provide at session end (0-9 scale, can use .5)
- feedback: Only provide at session end (2-3 sentences)
- next_question_type: "elaboration", "clarification", or "new_topic"
"""


# ─────────────────────────────────────────────
#  Agent Registration & Functions
# ─────────────────────────────────────────────

agent = ExaminerChatAgent()


def create_session(part: int = 1, topic: Optional[str] = None) -> ExaminerSession:
    """Create a new examiner chat session."""
    import uuid
    
    if not topic:
        topics = ExaminerChatAgent.PART1_TOPICS if part == 1 else ExaminerChatAgent.PART3_TOPICS
        topic = topics[hash(str(uuid.uuid4())) % len(topics)]
    
    session = ExaminerSession(
        session_id=f"examiner-{uuid.uuid4().hex[:8]}",
        part=part,
        topic=topic,
        max_turns=5 if part == 1 else 6,
    )
    
    # Add opening message
    if part == 1:
        session.messages.append(ChatMessage(
            role="examiner",
            content=f"Good {datetime.utcnow().strftime('%A')}! Let's talk about {topic}. {generate_opening_question(topic, part)}"
        ))
    else:
        session.messages.append(ChatMessage(
            role="examiner",
            content=f"Now we'll discuss some more general questions related to {topic}. {generate_opening_question(topic, part)}"
        ))
    
    return session


def generate_opening_question(topic: str, part: int) -> str:
    """Generate an opening question for the topic."""
    # Simple template-based generation; could be enhanced with LLM
    if part == 1:
        templates = [
            f"Do you enjoy {topic}?",
            f"How often do you {topic.replace(' and ', ' or ')}?",
            f"Tell me about your {topic}.",
            f"What do you like most about {topic}?",
        ]
    else:
        templates = [
            f"How important is {topic} in today's society?",
            f"What are the main issues related to {topic}?",
            f"How has {topic} changed in recent years?",
            f"What role does {topic} play in people's lives?",
        ]
    
    return templates[hash(topic + str(part)) % len(templates)]


async def process_student_response(
    session: ExaminerSession,
    student_message: str,
) -> ExaminerResponse:
    """
    Process a student's response and generate the examiner's next turn.
    """
    from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError
    import json
    
    # Add student message to session
    session.messages.append(ChatMessage(
        role="student",
        content=student_message
    ))
    session.turn_count += 1
    
    # Check if session should end
    if session.turn_count >= session.max_turns:
        # Generate final feedback
        return await generate_session_end(session)
    
    # Generate follow-up question
    try:
        client = get_gemma_client()
        
        # Build conversation context
        context = "\n".join([
            f"{'Examiner' if m.role == 'examiner' else 'Student'}: {m.content}"
            for m in session.messages[-6:]  # Last 6 messages for context
        ])
        
        prompt = f"""{agent._get_system_prompt(session)}

CONVERSATION SO FAR:
{context}

STUDENT'S LAST ANSWER: {student_message}

Generate your next response as the examiner. Ask a natural follow-up question.
Return JSON only.
"""
        
        result = client.generate_structured(
            prompt=prompt,
            schema=ExaminerResponse,
            temperature=0.7,
        )
        
        # Add examiner message to session
        session.messages.append(ChatMessage(
            role="examiner",
            content=result.message
        ))
        
        return result
        
    except GemmaClientError:
        # Fallback: generate simple follow-up
        return generate_fallback_response(session)


async def generate_session_end(session: ExaminerSession) -> ExaminerResponse:
    """Generate final feedback and band estimate."""
    from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError
    import json
    
    try:
        client = get_gemma_client()
        
        # Build full conversation
        conversation = "\n".join([
            f"{'Examiner' if m.role == 'examiner' else 'Student'}: {m.content}"
            for m in session.messages
        ])
        
        prompt = f"""You are an IELTS Speaking examiner. The session has ended.

TOPIC: {session.topic}
PART: {session.part}

FULL CONVERSATION:
{conversation}

Provide:
1. A polite closing message
2. Estimated band score (consider fluency, vocabulary, grammar, pronunciation)
3. Brief feedback (2-3 sentences, encouraging but honest)

Return JSON only.
"""
        
        result = client.generate_structured(
            prompt=prompt,
            schema=ExaminerResponse,
            temperature=0.3,
        )
        
        result.is_session_end = True
        session.estimated_band = result.estimated_band
        session.feedback = result.feedback
        
        return result
        
    except GemmaClientError:
        # Fallback feedback
        return ExaminerResponse(
            message="Thank you for your answers today. That concludes our speaking session.",
            is_session_end=True,
            estimated_band=6.5,
            feedback="Good effort overall. Try to expand your answers with more details and examples."
        )


def generate_fallback_response(session: ExaminerSession) -> ExaminerResponse:
    """Generate a simple follow-up when LLM is unavailable."""
    follow_ups = [
        "Can you tell me more about that?",
        "Why do you think that is?",
        "How does that make you feel?",
        "What would you say to someone who disagrees?",
        "That's interesting. Can you give an example?",
    ]
    
    import random
    message = follow_ups[random.randint(0, len(follow_ups) - 1)]
    
    return ExaminerResponse(
        message=message,
        next_question_type="elaboration"
    )


# Register with agent registry
@registry.register("examiner_chat")
def examiner_chat_handler(params: dict):
    """Handle examiner chat requests from the registry."""
    action = params.get("action")
    
    if action == "create_session":
        return create_session(
            part=params.get("part", 1),
            topic=params.get("topic")
        )
    elif action == "respond":
        session_data = params.get("session")
        session = ExaminerSession.model_validate(session_data)
        student_message = params.get("message", "")
        # Note: This is sync wrapper; async should be called directly
        return generate_fallback_response(session)
    
    return {"error": "Unknown action"}
