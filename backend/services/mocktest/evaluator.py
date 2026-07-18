"""
AI-powered evaluation engine for mock tests.
Produces comprehensive diagnostic reports after all sections are complete.
"""
import asyncio
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field

from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError
from services.mocktest.main import _score_to_band

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Diagnostic Report Schema
# ═══════════════════════════════════════════════════════════════════════════════

class VocabularyAnalysis(BaseModel):
    cefr_level: str = Field(description="Detected CEFR level: A2/B1/B2/C1/C2")
    lexical_diversity_score: float = Field(description="0-100 score for vocabulary range")
    academic_word_percentage: float = Field(description="% of academic vocabulary used")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class GrammarAnalysis(BaseModel):
    error_rate: float = Field(description="Errors per 100 words")
    sentence_complexity: dict = Field(
        description="Distribution: simple/compound/complex percentages"
    )
    common_mistakes: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)


class TimeAnalysis(BaseModel):
    listening_time: dict = Field(description="allocated vs spent")
    reading_time: dict = Field(description="allocated vs spent")
    writing_time: dict = Field(description="allocated vs spent")
    speaking_time: dict = Field(description="allocated vs spent")
    rushed_sections: list[str] = Field(default_factory=list)
    slow_sections: list[str] = Field(default_factory=list)


class QuestionTypeBreakdown(BaseModel):
    question_type: str
    total: int
    correct: int
    accuracy_percent: float


class DiagnosticReport(BaseModel):
    """Comprehensive AI diagnostic report for a mock test."""
    # Band scores
    overall_band: float
    listening_band: float
    reading_band: float
    writing_band: float
    speaking_band: float

    # Detailed analysis
    vocabulary_analysis: VocabularyAnalysis
    grammar_analysis: GrammarAnalysis
    time_analysis: TimeAnalysis
    question_type_breakdown: list[QuestionTypeBreakdown]

    # Strengths and weaknesses
    top_strengths: list[str]
    key_weaknesses: list[str]

    # Comparison and recommendations
    target_band_gap: Optional[float] = None
    estimated_weeks_to_target: Optional[int] = None
    recommended_focus_areas: list[str]
    study_plan_adjustments: list[str]

    # Summary
    summary_text: str


# ═══════════════════════════════════════════════════════════════════════════════
# EVALUATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def evaluate_mock_test(
    sections: list,
    target_band: float = 7.0,
) -> dict:
    """
    Run full diagnostic evaluation on a completed mock test.
    Combines objective scoring with AI analysis of writing/speaking.

    Args:
        sections: List of MockTestSection objects (all completed)
        target_band: User's target band score

    Returns:
        Full diagnostic report as dict
    """
    # Collect section data
    section_map = {s.section_type: s for s in sections}

    # Score objective sections (listening, reading)
    listening_band = float(section_map["listening"].band_estimate or 0)
    reading_band = float(section_map["reading"].band_estimate or 0)

    # Score writing and speaking via AI
    writing_band = await _evaluate_writing(section_map.get("writing"))
    speaking_band = await _evaluate_speaking(section_map.get("speaking"))

    # Calculate overall band (IELTS formula: average rounded to nearest 0.5)
    raw_avg = (listening_band + reading_band + writing_band + speaking_band) / 4
    overall_band = round(raw_avg * 2) / 2  # Round to nearest 0.5

    # Build time analysis
    time_analysis = _build_time_analysis(section_map)

    # Build question type breakdown
    question_breakdown = _build_question_type_breakdown(section_map)

    # Run AI diagnostic analysis
    ai_report = await _run_ai_diagnostic(
        section_map=section_map,
        overall_band=overall_band,
        listening_band=listening_band,
        reading_band=reading_band,
        writing_band=writing_band,
        speaking_band=speaking_band,
        target_band=target_band,
    )

    # Assemble final report
    report = {
        "overall_band": overall_band,
        "listening_band": listening_band,
        "reading_band": reading_band,
        "writing_band": writing_band,
        "speaking_band": speaking_band,
        "vocabulary_analysis": ai_report.get("vocabulary_analysis", _default_vocab_analysis()),
        "grammar_analysis": ai_report.get("grammar_analysis", _default_grammar_analysis()),
        "time_analysis": time_analysis,
        "question_type_breakdown": question_breakdown,
        "top_strengths": ai_report.get("top_strengths", []),
        "key_weaknesses": ai_report.get("key_weaknesses", []),
        "target_band_gap": round(target_band - overall_band, 1),
        "estimated_weeks_to_target": ai_report.get("estimated_weeks_to_target"),
        "recommended_focus_areas": ai_report.get("recommended_focus_areas", []),
        "study_plan_adjustments": ai_report.get("study_plan_adjustments", []),
        "summary_text": ai_report.get("summary_text", f"Overall band: {overall_band}"),
    }

    return report


# ═══════════════════════════════════════════════════════════════════════════════
# WRITING EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

async def _evaluate_writing(section) -> float:
    """Evaluate writing section using AI. Returns band estimate."""
    if not section or not section.answers:
        return 5.0  # Default if no writing submitted

    answers = section.answers
    task1_essay = answers.get("task_1", "")
    task2_essay = answers.get("task_2", "")

    if not task1_essay and not task2_essay:
        return 5.0

    prompt = f"""You are an expert IELTS Writing examiner. Score these essays.

TASK 1 ESSAY ({len(task1_essay.split())} words):
{task1_essay[:2000]}

TASK 2 ESSAY ({len(task2_essay.split())} words):
{task2_essay[:3000]}

Score each on IELTS criteria (1-9):
- Task Achievement / Task Response
- Coherence and Cohesion
- Lexical Resource
- Grammatical Range and Accuracy

Calculate the overall Writing band score.
Task 2 is weighted more heavily (2/3 of the final score).

Return ONLY a JSON object:
{{
    "task_1_band": float,
    "task_2_band": float,
    "overall_writing_band": float,
    "criteria": {{
        "task_response": float,
        "coherence": float,
        "lexical_resource": float,
        "grammar": float
    }},
    "key_feedback": ["point1", "point2", "point3"]
}}"""

    try:
        client = get_gemma_client()
        response = await asyncio.to_thread(client.generate_text, prompt, None, 0.2)
        parsed = _parse_json(response)
        if parsed and "overall_writing_band" in parsed:
            # Store feedback in section
            if section:
                section.section_feedback = parsed
            return float(parsed["overall_writing_band"])
    except (GemmaClientError, Exception) as e:
        logger.error(f"Writing evaluation failed: {e}")

    # Fallback: estimate based on word count
    total_words = len(task1_essay.split()) + len(task2_essay.split())
    if total_words >= 400:
        return 6.0
    elif total_words >= 250:
        return 5.5
    return 5.0


# ═══════════════════════════════════════════════════════════════════════════════
# SPEAKING EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

async def _evaluate_speaking(section) -> float:
    """Evaluate speaking section using AI transcription analysis. Returns band estimate."""
    if not section or not section.answers:
        return 5.0

    answers = section.answers
    # Speaking answers contain transcriptions of user recordings
    transcripts = []
    for part_key in ["part_1", "part_2", "part_3"]:
        part_data = answers.get(part_key, {})
        if isinstance(part_data, dict):
            for q_key, transcript in part_data.items():
                if transcript:
                    transcripts.append(f"[{part_key}/{q_key}]: {transcript}")
        elif isinstance(part_data, str):
            transcripts.append(f"[{part_key}]: {part_data}")

    if not transcripts:
        return 5.0

    all_text = "\n".join(transcripts)

    prompt = f"""You are an expert IELTS Speaking examiner. Evaluate these speaking responses.

TRANSCRIPTS:
{all_text[:4000]}

Score on IELTS criteria (1-9):
- Fluency and Coherence
- Lexical Resource
- Grammatical Range and Accuracy
- Pronunciation (infer from text patterns, fillers, and self-corrections)

Return ONLY a JSON object:
{{
    "overall_speaking_band": float,
    "criteria": {{
        "fluency": float,
        "lexical_resource": float,
        "grammar": float,
        "pronunciation": float
    }},
    "key_feedback": ["point1", "point2", "point3"]
}}"""

    try:
        client = get_gemma_client()
        response = await asyncio.to_thread(client.generate_text, prompt, None, 0.2)
        parsed = _parse_json(response)
        if parsed and "overall_speaking_band" in parsed:
            if section:
                section.section_feedback = parsed
            return float(parsed["overall_speaking_band"])
    except (GemmaClientError, Exception) as e:
        logger.error(f"Speaking evaluation failed: {e}")

    # Fallback: estimate based on transcript length/complexity
    word_count = len(all_text.split())
    if word_count >= 500:
        return 6.0
    elif word_count >= 200:
        return 5.5
    return 5.0


# ═══════════════════════════════════════════════════════════════════════════════
# FULL AI DIAGNOSTIC
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_ai_diagnostic(
    section_map: dict,
    overall_band: float,
    listening_band: float,
    reading_band: float,
    writing_band: float,
    speaking_band: float,
    target_band: float,
) -> dict:
    """Run comprehensive AI diagnostic analysis."""
    # Gather writing text for vocabulary/grammar analysis
    writing_text = ""
    writing_section = section_map.get("writing")
    if writing_section and writing_section.answers:
        writing_text = (
            writing_section.answers.get("task_1", "") + "\n" +
            writing_section.answers.get("task_2", "")
        )

    # Gather speaking transcripts
    speaking_text = ""
    speaking_section = section_map.get("speaking")
    if speaking_section and speaking_section.answers:
        for part_key in ["part_1", "part_2", "part_3"]:
            part_data = speaking_section.answers.get(part_key, {})
            if isinstance(part_data, dict):
                speaking_text += " ".join(part_data.values()) + " "
            elif isinstance(part_data, str):
                speaking_text += part_data + " "

    # Build question accuracy summary
    q_breakdown = _build_question_type_breakdown(section_map)
    q_summary = "\n".join([
        f"- {q['question_type']}: {q['correct']}/{q['total']} ({q['accuracy_percent']:.0f}%)"
        for q in q_breakdown
    ])

    combined_text = (writing_text + " " + speaking_text).strip()

    prompt = f"""You are an expert IELTS diagnostic analyst. Produce a comprehensive analysis.

SCORES:
- Overall Band: {overall_band}
- Listening: {listening_band}
- Reading: {reading_band}
- Writing: {writing_band}
- Speaking: {speaking_band}
- Target Band: {target_band}
- Gap to Target: {target_band - overall_band:.1f}

QUESTION TYPE ACCURACY:
{q_summary}

WRITING + SPEAKING TEXT SAMPLE (for vocabulary/grammar analysis):
{combined_text[:3000]}

Produce a diagnostic report. Return ONLY valid JSON:
{{
    "vocabulary_analysis": {{
        "cefr_level": "B1|B2|C1|C2",
        "lexical_diversity_score": 0-100,
        "academic_word_percentage": 0-100,
        "strengths": ["str1", "str2"],
        "weaknesses": ["str1", "str2"]
    }},
    "grammar_analysis": {{
        "error_rate": errors_per_100_words,
        "sentence_complexity": {{"simple": pct, "compound": pct, "complex": pct}},
        "common_mistakes": ["mistake1", "mistake2"],
        "strengths": ["str1", "str2"]
    }},
    "top_strengths": ["strength1", "strength2", "strength3"],
    "key_weaknesses": ["weakness1", "weakness2", "weakness3"],
    "estimated_weeks_to_target": integer_or_null,
    "recommended_focus_areas": ["area1", "area2", "area3"],
    "study_plan_adjustments": ["adjustment1", "adjustment2", "adjustment3"],
    "summary_text": "2-3 sentence overall summary of performance and next steps"
}}"""

    try:
        client = get_gemma_client()
        response = await asyncio.to_thread(client.generate_text, prompt, None, 0.3)
        parsed = _parse_json(response)
        if parsed:
            return parsed
    except (GemmaClientError, Exception) as e:
        logger.error(f"AI diagnostic failed: {e}")

    # Fallback diagnostic
    return _fallback_diagnostic(
        overall_band, listening_band, reading_band,
        writing_band, speaking_band, target_band
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_time_analysis(section_map: dict) -> dict:
    """Build time analysis comparing allocated vs spent."""
    analysis = {}
    rushed = []
    slow = []

    for section_type in ["listening", "reading", "writing", "speaking"]:
        section = section_map.get(section_type)
        if section:
            allocated = section.time_allocated_seconds
            spent = section.time_spent_seconds or 0
            analysis[f"{section_type}_time"] = {
                "allocated_seconds": allocated,
                "spent_seconds": spent,
                "percentage_used": round((spent / allocated * 100), 1) if allocated else 0,
            }
            if spent < allocated * 0.5:
                rushed.append(section_type)
            elif spent > allocated * 0.95:
                slow.append(section_type)

    analysis["rushed_sections"] = rushed
    analysis["slow_sections"] = slow
    return analysis


def _build_question_type_breakdown(section_map: dict) -> list[dict]:
    """Build accuracy breakdown per question type."""
    type_stats = {}  # type -> {correct, total}

    for section_type in ["listening", "reading"]:
        section = section_map.get(section_type)
        if not section or not section.content_data or not section.answers:
            continue

        answers = section.answers
        if section_type == "listening":
            items = section.content_data.get("sections", [])
            for item in items:
                for q in item.get("questions", []):
                    qtype = q.get("type", "UNKNOWN")
                    if qtype not in type_stats:
                        type_stats[qtype] = {"correct": 0, "total": 0}
                    type_stats[qtype]["total"] += 1
                    user_ans = str(answers.get(str(q["id"]), "")).strip().lower()
                    correct = str(q["correct_answer"]).strip().lower()
                    if user_ans == correct:
                        type_stats[qtype]["correct"] += 1

        elif section_type == "reading":
            passages = section.content_data.get("passages", [])
            for passage in passages:
                for q in passage.get("questions", []):
                    qtype = q.get("type", "UNKNOWN")
                    if qtype not in type_stats:
                        type_stats[qtype] = {"correct": 0, "total": 0}
                    type_stats[qtype]["total"] += 1
                    user_ans = str(answers.get(str(q["id"]), "")).strip().lower()
                    correct = str(q["correct_answer"]).strip().lower()
                    if user_ans == correct:
                        type_stats[qtype]["correct"] += 1

    return [
        {
            "question_type": qtype,
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy_percent": round(
                (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1
            ),
        }
        for qtype, stats in sorted(type_stats.items())
    ]


def _parse_json(response: str) -> Optional[dict]:
    """Extract JSON from AI response."""
    if not response:
        return None
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            try:
                return json.loads(response[start:end].strip())
            except json.JSONDecodeError:
                pass
    if "{" in response:
        start = response.find("{")
        end = response.rfind("}") + 1
        if end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass
    return None


def _default_vocab_analysis() -> dict:
    return {
        "cefr_level": "B2",
        "lexical_diversity_score": 50.0,
        "academic_word_percentage": 10.0,
        "strengths": ["Basic vocabulary is adequate"],
        "weaknesses": ["Limited academic vocabulary range"],
    }


def _default_grammar_analysis() -> dict:
    return {
        "error_rate": 5.0,
        "sentence_complexity": {"simple": 50, "compound": 30, "complex": 20},
        "common_mistakes": ["Subject-verb agreement", "Article usage"],
        "strengths": ["Basic sentence structures are correct"],
    }


def _fallback_diagnostic(
    overall: float, listening: float, reading: float,
    writing: float, speaking: float, target: float,
) -> dict:
    """Generate a fallback diagnostic when AI is unavailable."""
    gap = target - overall
    weakest = min(
        [("listening", listening), ("reading", reading),
         ("writing", writing), ("speaking", speaking)],
        key=lambda x: x[1]
    )
    strongest = max(
        [("listening", listening), ("reading", reading),
         ("writing", writing), ("speaking", speaking)],
        key=lambda x: x[1]
    )

    return {
        "vocabulary_analysis": _default_vocab_analysis(),
        "grammar_analysis": _default_grammar_analysis(),
        "top_strengths": [
            f"Strong {strongest[0]} skills (Band {strongest[1]})",
            "Completed full test under timed conditions",
            "Good test stamina",
        ],
        "key_weaknesses": [
            f"{weakest[0].capitalize()} needs improvement (Band {weakest[1]})",
            f"Gap of {gap:.1f} bands to target",
            "Consider more focused practice on weak areas",
        ],
        "estimated_weeks_to_target": max(4, int(gap * 8)) if gap > 0 else None,
        "recommended_focus_areas": [
            weakest[0].capitalize(),
            "Academic vocabulary",
            "Time management",
        ],
        "study_plan_adjustments": [
            f"Dedicate extra time to {weakest[0]} practice",
            "Review question types with lowest accuracy",
            "Practice under timed conditions regularly",
        ],
        "summary_text": (
            f"Your overall band score is {overall}, with {strongest[0]} as your "
            f"strongest skill ({strongest[1]}) and {weakest[0]} needing the most "
            f"attention ({weakest[1]}). {'You are on track to reach your target.' if gap <= 0.5 else f'Focus on closing the {gap:.1f} band gap to your target of {target}.'}"
        ),
    }
