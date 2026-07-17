"""
SocraticHintAgent — multi-turn Socratic Debugging Engine.

Instead of showing the correct answer immediately, this agent guides the
student to find the semantic mismatch on their own through structured questions.

Behaviour loop:
  Turn 1 (hint_level=1) — Point to the relevant paragraph, ask what they notice.
  Turn 2 (hint_level=2) — Focus on the specific word/qualifier that changes meaning.
  Turn 3 (hint_level=3) — Near-explicit prompt that leads them logically to the answer.

  On any turn: if the student's reply shows genuine understanding,
  set breakthrough_confirmed=True and celebrate.

Rules:
  - NEVER reveal the correct answer directly.
  - NEVER include the correct answer string in hint_text.
  - Ask exactly ONE question per turn.
  - next_action drives the UI state machine on the frontend.
"""
from typing import Literal
from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry


# ─────────────────────────────────────────────
#  I/O schemas
# ─────────────────────────────────────────────

class ConversationTurn(BaseModel):
    role: Literal["agent", "student"]
    text: str


class SocraticHintRequest(BaseModel):
    question_text: str
    correct_answer: str
    user_answer: str
    passage_excerpt: str            # Relevant paragraph(s), max ~600 chars
    question_type: str = "TRUE_FALSE_NOT_GIVEN"
    conversation_history: list[ConversationTurn] = []


class SocraticHintResponse(BaseModel):
    hint_text: str                  # The single guiding question (max 60 words)
    hint_level: int                 # 1 | 2 | 3
    cognitive_shift_detected: bool  # Did the student's last reply show understanding?
    breakthrough_confirmed: bool    # Student has found the answer on their own
    next_action: Literal["await_reply", "confirm_breakthrough", "reveal_answer"]


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class SocraticHintAgent(BaseAgent):
    name = "SocraticHintAgent"
    description = "Guides students to correct reading answers through structured questioning without revealing the answer."

    def _compute_hint_level(self, history: list[ConversationTurn]) -> int:
        """Hint level = number of completed student turns + 1, capped at 3."""
        student_turns = sum(1 for t in history if t.role == "student")
        return min(student_turns + 1, 3)

    def _format_history(self, history: list[ConversationTurn]) -> str:
        if not history:
            return ""
        lines = [
            f"{'Uma' if t.role == 'agent' else 'Student'}: {t.text}"
            for t in history[-4:]   # last 4 turns maximum
        ]
        return "\nCONVERSATION SO FAR:\n" + "\n".join(lines)

    def _last_student_reply(self, history: list[ConversationTurn]) -> str:
        for turn in reversed(history):
            if turn.role == "student":
                return turn.text
        return ""

    def _build_prompt(self, request: SocraticHintRequest) -> str:
        hint_level = self._compute_hint_level(request.conversation_history)
        history_str = self._format_history(request.conversation_history)
        last_reply = self._last_student_reply(request.conversation_history)

        return f"""You are the SOCRATIC DEBUGGING AGENT for an IELTS reading tutor named Uma.
A student answered a question incorrectly. Guide them to the correct answer without revealing it.

STRICT RULES:
1. NEVER state the correct answer directly.
2. NEVER include the text "{request.correct_answer}" in your hint.
3. Ask exactly ONE guiding question per response. Maximum 60 words.
4. Hint level {hint_level} guidance:
   {self._level_guidance(hint_level)}
5. If the student's last reply shows they understand, set breakthrough_confirmed=true.
6. After breakthrough: set next_action="confirm_breakthrough".
7. At hint_level=3 without breakthrough: set next_action="reveal_answer".
8. Otherwise: set next_action="await_reply".

QUESTION: {request.question_text}
STUDENT ANSWERED: {request.user_answer} (WRONG)
CORRECT ANSWER:   {request.correct_answer}
QUESTION TYPE:    {request.question_type}

PASSAGE EXCERPT:
{request.passage_excerpt[:600]}
{history_str}
LAST STUDENT REPLY: "{last_reply}"

HINT LEVEL: {hint_level}/3

Evaluate whether the last student reply shows genuine understanding (cognitive_shift_detected).
Return JSON matching SocraticHintResponse schema exactly. No commentary outside the JSON."""

    @staticmethod
    def _level_guidance(level: int) -> str:
        guidance = {
            1: "Point gently to the relevant paragraph. Ask what they notice about the author's language.",
            2: "Focus on the specific word, qualifier, or modifier that changes the meaning (e.g. 'potentially', 'seldom', 'unlike'). Ask what it implies.",
            3: "Give a near-explicit logical chain. E.g. 'If X is only described as possible, not confirmed, which answer type fits — True, False, or Not Given?'",
        }
        return guidance.get(level, guidance[3])

    async def get_hint(self, request: SocraticHintRequest) -> SocraticHintResponse:
        return await self.run_structured(
            prompt=self._build_prompt(request),
            schema=SocraticHintResponse,
            temperature=0.3,
        )
