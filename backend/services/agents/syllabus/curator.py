"""
SyllabusCuratorAgent — Autonomous background study planner.

Reads the student's aggregated performance telemetry, identifies the
single highest-leverage weakness, and generates:
  - A personalised Uma insight message for the dashboard
  - A prioritised task list rewritten around the weakness
  - A specific drill topic + question type for the next auto-generated test

Runs AFTER every session submission (fire-and-forget from the profile endpoint).
The result is stored in user.ava_intervention and surfaced on the dashboard.
"""
from typing import Optional
from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry


# ─────────────────────────────────────────────
#  Input schema
# ─────────────────────────────────────────────

class SkillTelemetrySummary(BaseModel):
    """Aggregated cross-skill performance data from the backend analytics layer."""
    # Reading
    reading_band: float = 0.0
    reading_sessions: int = 0
    reading_wrong_question_types: list[str] = []
    reading_avg_time_per_question_ms: float = 0.0
    reading_low_confidence_wins: int = 0
    reading_passage_friction_avg: float = 0.0

    # Writing
    writing_band: float = 0.0
    writing_sessions: int = 0
    writing_weak_criteria: list[str] = []

    # Listening
    listening_band: float = 0.0
    listening_sessions: int = 0
    listening_avg_seek_count: float = 0.0

    # Speaking
    speaking_band: float = 0.0
    speaking_sessions: int = 0
    speaking_filler_count_avg: float = 0.0

    # Cross-skill
    target_band: float = 7.0
    exam_date_days_remaining: Optional[int] = None


# ─────────────────────────────────────────────
#  Output schemas
# ─────────────────────────────────────────────

class RoadmapTask(BaseModel):
    title: str
    skill: str          # reading | writing | listening | speaking | vocabulary | grammar
    description: str    # One sentence describing the task
    priority: int       # 1 = highest


class UmaIntervention(BaseModel):
    """The structured output displayed on the student's dashboard."""
    headline: str                         # Short hook (max 12 words)
    insight_text: str                     # 2–3 sentence data-driven analysis
    targeted_skill: str                   # The skill this intervention targets
    weak_pattern_identified: str          # Exact pattern, e.g. "negative qualifiers like 'seldom'"
    recommended_tasks: list[RoadmapTask]  # 3–5 prioritised tasks
    drill_topic: str                      # Gemma topic for next auto-generated test
    drill_question_type: str              # IELTS question type to focus on


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class SyllabusCuratorAgent(BaseAgent):
    name = "SyllabusCuratorAgent"
    description = "Analyses cross-skill telemetry and autonomously rewrites the student's roadmap to target their highest-leverage weakness."

    def _build_prompt(self, telemetry: SkillTelemetrySummary) -> str:
        days_note = (
            f"The student has {telemetry.exam_date_days_remaining} days until their exam."
            if telemetry.exam_date_days_remaining else "No exam date set."
        )
        return f"""You are the AUTONOMOUS SYLLABUS CURATING AGENT for an IELTS AI tutor.
You have full access to the student's performance telemetry. Your job:
1. Identify the single highest-leverage weakness to address before exam day.
2. Write Uma's personalised dashboard message.
3. Generate a targeted task list (3–5 tasks) that directly addresses the weakness.
4. Specify the next auto-generated test's drill topic and question type.

STUDENT PERFORMANCE DATA:
- Target Band: {telemetry.target_band}
- {days_note}

Reading  → Band {telemetry.reading_band} over {telemetry.reading_sessions} sessions
  Wrong answer types: {', '.join(telemetry.reading_wrong_question_types) or 'none yet'}
  Avg time/question:  {round(telemetry.reading_avg_time_per_question_ms / 1000, 1)}s
  Low-confidence wins: {telemetry.reading_low_confidence_wins}
  Avg passage scrollbacks: {round(telemetry.reading_passage_friction_avg, 1)}

Writing  → Band {telemetry.writing_band} over {telemetry.writing_sessions} sessions
  Weak criteria: {', '.join(telemetry.writing_weak_criteria) or 'none yet'}

Listening → Band {telemetry.listening_band} over {telemetry.listening_sessions} sessions
  Avg seeks/session: {round(telemetry.listening_avg_seek_count, 1)}

Speaking → Band {telemetry.speaking_band} over {telemetry.speaking_sessions} sessions
  Avg filler words/recording: {round(telemetry.speaking_filler_count_avg, 1)}

OUTPUT REQUIREMENTS:
- headline: punchy, ≤12 words. Address the student directly ("Your…" or "I noticed…").
- insight_text: 2–3 sentences. Be specific — name the exact linguistic pattern.
  E.g. "passive inverted conditionals", "negative qualifiers like 'seldom'", "synonym traps".
- targeted_skill: one of reading | writing | listening | speaking.
- weak_pattern_identified: the exact pattern string (used as a searchable tag).
- recommended_tasks: 3–5 tasks, each targeting the weak pattern directly.
- drill_topic: a specific topic for Gemma to use when generating the next test
  (e.g. "urban planning", "marine biology", "fintech regulation").
- drill_question_type: exact IELTS question type string
  (e.g. TRUE_FALSE_NOT_GIVEN, MATCHING_HEADINGS, MULTIPLE_CHOICE).

Return JSON matching UmaIntervention schema exactly. No commentary outside the JSON."""

    async def analyse(self, telemetry: SkillTelemetrySummary) -> UmaIntervention:
        return await self.run_structured(
            prompt=self._build_prompt(telemetry),
            schema=UmaIntervention,
            temperature=0.4,
        )
