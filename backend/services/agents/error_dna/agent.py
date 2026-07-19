"""
ErrorDNAAgent — Cross-module mistake pattern clustering.

Reads the student's aggregated error profile from the analytics layer,
identifies recurring error signatures, and generates:
  - A weekly insight message for the dashboard
  - Labeled error patterns with evidence
  - Recommendations for targeted practice

Runs weekly (Monday batch) or on-demand.
"""
from typing import Optional
from pydantic import BaseModel

from services.agents.base import BaseAgent
from services.agents.registry import registry


# ─────────────────────────────────────────────
#  Output Schemas
# ─────────────────────────────────────────────

class SignatureItem(BaseModel):
    """A single identified error signature."""
    skill: str                          # reading | listening | writing | speaking | grammar
    question_type: Optional[str] = None
    error_type: Optional[str] = None
    pattern_label: str                  # Human-readable: "T/F/NG negative qualifier traps"
    pattern_key: str                    # Normalized key for DB: "reading_tfn_negative_qualifier"
    severity: str = "medium"            # low | medium | high
    occurrences: int = 1
    evidence: list[str] = []            # Example mistakes showing this pattern
    recommendation: str = ""            # What to practice


class ErrorDNAResult(BaseModel):
    """Complete Error DNA analysis output."""
    headline: str                       # Short hook for dashboard (max 12 words)
    insight_text: str                   # 2-3 sentence data-driven analysis
    signatures: list[SignatureItem]     # Identified error patterns (top 5-7)
    weak_pattern_identified: str        # Primary pattern to address
    recommended_focus: str              # Skill/question type to prioritize
    micro_drill_topic: Optional[str] = None  # Topic for generated exercises


# ─────────────────────────────────────────────
#  Agent
# ─────────────────────────────────────────────

@registry.register
class ErrorDNAAgent(BaseAgent):
    name = "ErrorDNAAgent"
    description = "Analyses cross-module error profiles and identifies recurring mistake patterns for targeted practice."

    def _build_prompt(self, error_profile: dict) -> str:
        """Build the analysis prompt from the error profile."""
        
        # Extract key metrics for the prompt
        reading_errors = error_profile.get("reading", {})
        listening_errors = error_profile.get("listening", {})
        writing_errors = error_profile.get("writing", {})
        speaking_errors = error_profile.get("speaking", {})
        grammar_errors = error_profile.get("grammar", {})
        
        top_patterns = error_profile.get("top_error_patterns", [])
        weakest_skill = error_profile.get("weakest_skill", "unknown")
        target_band = error_profile.get("target_band", 7.0)
        
        # Format patterns for prompt
        patterns_text = ""
        for i, p in enumerate(top_patterns[:10], 1):
            patterns_text += f"""
  {i}. {p.get('skill', 'unknown').upper()}: {p.get('pattern_label', p.get('question_type', 'unknown'))}
     Question Type: {p.get('question_type', 'N/A')}
     Error Type: {p.get('error_type', 'N/A')}
     Occurrences: {p.get('count', 0)}
     Examples: {len(p.get('recent_examples', []))} recorded"""

        return f"""You are the ERROR DNA ANALYSIS AGENT for an IELTS AI tutor.

You have full access to the student's cross-module error telemetry. Your job:
1. Identify 3-7 recurring error signatures with precise linguistic labels
2. Write a punchy dashboard headline and 2-3 sentence insight
3. Recommend the highest-leverage focus area for the next week

STUDENT ERROR PROFILE:

TOP ERROR PATTERNS:
{patterns_text}

SUMMARY:
- Weakest skill: {weakest_skill}
- Target band: {target_band}

READING: {reading_errors.get('total_errors', 0)} errors across {reading_errors.get('total_correct', 0) + reading_errors.get('total_errors', 0)} questions
LISTENING: {listening_errors.get('total_errors', 0)} errors across {listening_errors.get('total_correct', 0) + listening_errors.get('total_errors', 0)} questions
WRITING: {writing_errors.get('total_errors', 0)} weak criteria
SPEAKING: {speaking_errors.get('total_errors', 0)} weak criteria
GRAMMAR: {grammar_errors.get('total_errors', 0)} mistakes recorded

OUTPUT REQUIREMENTS:

1. headline: Punchy, ≤12 words. Address the student directly ("Your…" or "I noticed…").

2. insight_text: 2-3 sentences. Be specific — name the exact linguistic patterns.
   E.g. "You consistently miss T/F/NG questions when the text uses negative qualifiers like 'seldom' or 'rarely'."

3. signatures: 3-7 identified patterns. Each must have:
   - skill: reading | listening | writing | speaking | grammar
   - question_type: The IELTS question type (e.g., TRUE_FALSE_NOT_GIVEN, MATCHING_HEADINGS)
   - error_type: Category (e.g., comprehension, vocabulary, grammar_mistake)
   - pattern_label: Human-readable description (max 50 chars)
   - pattern_key: snake_case key for DB storage (e.g., "reading_tfn_negative_qualifier")
   - severity: low | medium | high
   - occurrences: Estimated count from the data
   - evidence: 1-3 example mistakes as short strings
   - recommendation: One specific practice action

4. weak_pattern_identified: The single most important pattern to address

5. recommended_focus: Skill + question type to prioritize (e.g., "reading TRUE_FALSE_NOT_GIVEN")

6. micro_drill_topic: A specific topic for generating targeted exercises (e.g., "negative qualifiers in academic texts")

Return JSON matching ErrorDNAResult schema exactly. No commentary outside the JSON."""

    async def analyse(self, error_profile: dict) -> ErrorDNAResult:
        """
        Analyze the cross-module error profile and identify signatures.
        
        Args:
            error_profile: Dict from CrossModuleErrorProfile.model_dump()
                           or from services.analytics.aggregation.build_cross_module_profile
        
        Returns:
            ErrorDNAResult with identified signatures and recommendations
        """
        return await self.run_structured(
            prompt=self._build_prompt(error_profile),
            schema=ErrorDNAResult,
            temperature=0.3,
        )

    async def analyse_from_aggregation(self, profile) -> ErrorDNAResult:
        """
        Convenience method to analyze directly from a CrossModuleErrorProfile.
        
        Args:
            profile: CrossModuleErrorProfile from aggregation layer
        
        Returns:
            ErrorDNAResult
        """
        # Convert Pydantic model to dict if needed
        if hasattr(profile, 'model_dump'):
            profile_dict = profile.model_dump()
        else:
            profile_dict = dict(profile)
        
        return await self.analyse(profile_dict)


# ─────────────────────────────────────────────
#  Micro-Exercise Generation
# ─────────────────────────────────────────────

class MicroExercise(BaseModel):
    """A single targeted exercise for a specific error pattern."""
    id: int
    question: str                      # The exercise question/prompt
    options: Optional[list[str]] = None  # For MCQ style exercises
    correct_answer: str
    explanation: str
    difficulty: str = "medium"         # easy | medium | hard


class MicroExerciseSet(BaseModel):
    """A set of micro-exercises targeting a specific error pattern."""
    pattern_key: str                   # Which signature this targets
    pattern_label: str
    skill: str
    question_type: str
    exercises: list[MicroExercise]     # 3-5 exercises
    strategy_tip: str                  # One key strategy to remember


class MicroExerciseRequest(BaseModel):
    """Request for generating micro-exercises."""
    signature: SignatureItem
    count: int = 5                     # Number of exercises to generate


async def generate_micro_exercises(request: MicroExerciseRequest) -> MicroExerciseSet:
    """
    Generate targeted micro-exercises for a specific error signature.
    
    This is a standalone function that uses the ErrorDNAAgent's LLM client
    to generate exercises that specifically address the identified pattern.
    
    Args:
        request: MicroExerciseRequest with signature and count
    
    Returns:
        MicroExerciseSet with 3-5 targeted exercises
    """
    from services.agents.base import BaseAgent
    
    class ExerciseGenerator(BaseAgent):
        name = "ExerciseGenerator"
        description = "Generates targeted micro-exercises for error patterns."
    
    generator = ExerciseGenerator()
    sig = request.signature
    
    prompt = f"""Generate {request.count} IELTS-style micro-exercises targeting this specific error pattern.

ERROR SIGNATURE:
- Skill: {sig.skill}
- Question Type: {sig.question_type or "general"}
- Pattern: {sig.pattern_label}
- Error Type: {sig.error_type or "comprehension"}
- Evidence of mistakes: {sig.evidence[:3] if sig.evidence else ["No specific examples"]}

REQUIREMENTS:
1. Each exercise must directly test the student's ability to avoid this error pattern
2. Use realistic IELTS-style content
3. For reading/listening: create {sig.question_type or "multiple-choice"} style questions
4. For grammar: create fill-in-the-blank or error-correction exercises
5. For writing/speaking: create guided practice prompts

Each exercise must have:
- id: Sequential number (1-{request.count})
- question: The exercise prompt (clear and specific)
- options: For MCQ, 4 options labeled A-D (optional for fill-blank)
- correct_answer: The correct answer
- explanation: Why this is correct and how it avoids the error pattern
- difficulty: easy | medium | hard

Also provide a strategy_tip: One key strategy the student should remember.

Return JSON matching MicroExerciseSet schema exactly:
{{
  "pattern_key": "{sig.pattern_key}",
  "pattern_label": "{sig.pattern_label}",
  "skill": "{sig.skill}",
  "question_type": "{sig.question_type or 'general'}",
  "exercises": [...],
  "strategy_tip": "..."
}}"""

    return await generator.run_structured(
        prompt=prompt,
        schema=MicroExerciseSet,
        temperature=0.5,
    )
