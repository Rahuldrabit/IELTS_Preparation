"""
AdversarialDistractorAgent — Targeted Cognitive Trap Generator.

Instead of generating generic exam questions, this agent analyses the
student's personal error history and intentionally rewrites or generates
new questions that contain the exact types of traps the student repeatedly
falls for.

How it works:
  1. Weakness mapping — caller passes the student's error history
     (mistake types, distractor patterns they fell for).
  2. Adversarial generation — the agent rewrites the question set so that:
     - Distractor options contain high-grade keyword traps matching their history.
     - Negative qualifiers (seldom, scarcely, rarely) appear near the answer zone.
     - Synonym traps replace obvious keywords with near-synonyms.
     - The passage and questions appear superficially easier than they are.
  3. Immunity building — repeated exposure builds structural immunity to each trap type.

Output contract:
  - Returns AdversarialQuestionSet with 3–5 questions targeting specific traps.
  - Each question includes a trap_type tag so the frontend can show "Trap Alert" badges.
"""
from typing import Optional, Literal
from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry


# ─────────────────────────────────────────────
#  Trap taxonomy (kept in one place for reuse)
# ─────────────────────────────────────────────

TrapType = Literal[
    "negative_qualifier",    # seldom, scarcely, rarely, barely
    "synonym_substitution",  # passage uses near-synonym, question uses original
    "partial_truth",         # statement is partially true but missing a key qualifier
    "temporal_mismatch",     # present tense in question vs past in passage
    "absolute_vs_hedge",     # "always"/"never" vs "sometimes"/"may"
    "scope_overreach",       # passage limits claim, question makes it universal
]

TRAP_DESCRIPTIONS: dict[str, str] = {
    "negative_qualifier":  "Uses words like 'seldom', 'scarcely', 'rarely' near the answer anchor.",
    "synonym_substitution": "Passage uses a near-synonym; question uses the original word as a distractor.",
    "partial_truth":       "The statement is partially supported but a critical qualifier is missing.",
    "temporal_mismatch":   "The tense in the question differs subtly from the passage.",
    "absolute_vs_hedge":   "The question uses an absolute term where the passage hedges.",
    "scope_overreach":     "The passage limits a claim to a subgroup; the question makes it universal.",
}


# ─────────────────────────────────────────────
#  I/O schemas
# ─────────────────────────────────────────────

class StudentWeaknessProfile(BaseModel):
    """
    Summary of what the student consistently falls for.
    Populated from their session history by the calling endpoint.
    """
    wrong_question_types: list[str] = []        # e.g. ["Inference", "Vocabulary"]
    distractor_patterns_fallen_for: list[str] = []   # e.g. ["negative_qualifier", "synonym_substitution"]
    low_confidence_win_topics: list[str] = []    # Topics where they guessed correctly
    avg_time_per_question_ms: float = 0.0
    target_band: float = 7.0


class AdversarialQuestion(BaseModel):
    question_id: int
    question_text: str
    answer_options: list[str]               # For TFNG: ["True", "False", "Not Given"]
    correct_answer: str
    trap_type: str                          # One of TrapType values
    trap_explanation: str                   # Why this is a trap (for review panel only)
    evidence_paragraph_hint: str            # e.g. "Paragraph B, third sentence"


class AdversarialQuestionSet(BaseModel):
    passage: str                            # A custom passage with traps embedded
    questions: list[AdversarialQuestion]    # 3–5 targeted questions
    trap_summary: str                       # E.g. "This set focuses on negative qualifiers and synonym traps."
    difficulty_label: str                   # "Targeted" | "Hard" | "Expert"


class AdversarialGenerationRequest(BaseModel):
    """Input to the agent."""
    weakness_profile: StudentWeaknessProfile
    topic: Optional[str] = None             # Optional topic override
    question_type: str = "TRUE_FALSE_NOT_GIVEN"
    num_questions: int = 4                  # 3–5


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class AdversarialDistractorAgent(BaseAgent):
    name = "AdversarialDistractorAgent"
    description = "Generates IELTS questions with traps that specifically target the student's personal cognitive blind spots."

    def _select_trap_types(self, profile: StudentWeaknessProfile) -> list[str]:
        """
        Map the student's weakness patterns to concrete trap types.
        Falls back to the two most common trap types if no history exists.
        """
        # Direct match from distractor history
        traps = [
            t for t in profile.distractor_patterns_fallen_for
            if t in TRAP_DESCRIPTIONS
        ]
        # Add trap types implied by wrong question types
        type_to_trap = {
            "Vocabulary":  "synonym_substitution",
            "Inference":   "partial_truth",
            "Distractor":  "absolute_vs_hedge",
            "Skim-Scan":   "scope_overreach",
            "Detail":      "temporal_mismatch",
        }
        for qtype in profile.wrong_question_types:
            mapped = type_to_trap.get(qtype)
            if mapped and mapped not in traps:
                traps.append(mapped)

        # Fallback
        if not traps:
            traps = ["negative_qualifier", "synonym_substitution"]

        return traps[:3]   # Cap at 3 distinct trap types per set

    def _build_prompt(self, request: AdversarialGenerationRequest) -> str:
        profile = request.weakness_profile
        traps = self._select_trap_types(profile)
        trap_list = "\n".join(
            f"  - {t}: {TRAP_DESCRIPTIONS[t]}"
            for t in traps
        )
        topic_line = f"Topic: {request.topic}" if request.topic else "Choose a topic related to science, environment, or society."

        return f"""You are the ADVERSARIAL DISTRACTOR AGENT for an IELTS AI tutor.
Your job: generate a reading passage and {request.num_questions} questions that contain
carefully designed traps matching this student's personal cognitive blind spots.

STUDENT WEAK SPOTS:
- Wrong question types: {', '.join(profile.wrong_question_types) or 'not recorded'}
- Trap patterns fallen for: {', '.join(profile.distractor_patterns_fallen_for) or 'not recorded'}

TRAP TYPES TO EMBED IN THIS SET:
{trap_list}

INSTRUCTIONS:
1. Write a 200–250 word reading passage.
   {topic_line}
   Embed the target trap patterns NATURALLY — the passage should not feel artificial.
   The traps must be subtle: a careful reader who knows the patterns would catch them,
   a careless reader would miss them.

2. Generate exactly {request.num_questions} {request.question_type} questions.
   Each question must:
   - Target one of the three trap types above.
   - Have an answer that seems obvious at first glance but requires careful reading.
   - Include an evidence_paragraph_hint telling the student where to look.
   - Include a trap_explanation (for review only) explaining WHY it's a trap.

3. Set difficulty_label based on how subtle the traps are:
   "Targeted" = clear traps, "Hard" = subtle, "Expert" = very subtle.

4. Write a trap_summary sentence explaining which traps appear in this set.

Return JSON matching AdversarialQuestionSet schema exactly.
No commentary outside the JSON."""

    async def generate(
        self,
        request: AdversarialGenerationRequest,
    ) -> AdversarialQuestionSet:
        return await self.run_structured(
            prompt=self._build_prompt(request),
            schema=AdversarialQuestionSet,
            temperature=0.5,    # Slightly higher for creative passage generation
        )
