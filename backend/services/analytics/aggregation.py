"""
Cross-Module Error Aggregation Layer.

Collects and normalizes error data across Reading, Listening, Writing, and Speaking
to feed the Error DNA agent and provide unified telemetry for the syllabus curator.
"""
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    Session,
    UserResponse,
    ReadingQuestion,
    ListeningQuestion,
    GrammarMistake,
    GrammarSkill,
    User,
)


# ─────────────────────────────────────────────
#  Output Schemas
# ─────────────────────────────────────────────

class ErrorPattern(BaseModel):
    """A normalized error pattern across skills."""
    skill: str                          # reading | listening | writing | speaking | grammar
    question_type: Optional[str] = None # IELTS question type or "grammar_mistake"
    error_type: Optional[str] = None    # mishearing, comprehension, grammar, etc.
    pattern_label: Optional[str] = None # Human-readable pattern name
    count: int = 0
    recent_examples: list[dict] = []    # Last 3-5 occurrences with context


class SkillErrorSummary(BaseModel):
    """Error summary for a single skill."""
    skill: str
    total_errors: int = 0
    total_correct: int = 0
    accuracy_rate: float = 0.0
    error_patterns: list[ErrorPattern] = []
    avg_time_per_question_ms: Optional[float] = None


class WritingFeedbackSummary(BaseModel):
    """Extracted writing criteria weaknesses."""
    task_response_avg: float = 0.0
    coherence_avg: float = 0.0
    lexical_avg: float = 0.0
    grammar_avg: float = 0.0
    sessions_count: int = 0
    weak_criteria: list[str] = []       # Criteria below band target


class SpeakingFeedbackSummary(BaseModel):
    """Extracted speaking feedback signals."""
    fluency_avg: float = 0.0
    lexical_avg: float = 0.0
    grammar_avg: float = 0.0
    pronunciation_avg: float = 0.0
    sessions_count: int = 0
    filler_count_avg: float = 0.0
    weak_criteria: list[str] = []


class CrossModuleErrorProfile(BaseModel):
    """Complete cross-module error profile for a user."""
    user_id: int
    period_start: datetime
    period_end: datetime
    
    # Per-skill summaries
    reading: SkillErrorSummary
    listening: SkillErrorSummary
    writing: SkillErrorSummary
    speaking: SkillErrorSummary
    grammar: SkillErrorSummary
    
    # Aggregated insights
    top_error_patterns: list[ErrorPattern] = []  # Top 5 across all skills
    weakest_skill: Optional[str] = None
    strongest_skill: Optional[str] = None
    
    # For SyllabusCuratorAgent compatibility
    target_band: float = 7.0
    exam_date_days_remaining: Optional[int] = None


# ─────────────────────────────────────────────
#  Aggregation Functions
# ─────────────────────────────────────────────

async def collect_reading_errors(
    user_id: int,
    db: AsyncSession,
    since: Optional[datetime] = None,
) -> SkillErrorSummary:
    """
    Collect error patterns from reading sessions.
    Groups by question_type and error_type.
    """
    since = since or datetime.utcnow() - timedelta(days=30)
    
    # Query UserResponse joined with Session and ReadingQuestion
    stmt = (
        select(UserResponse, Session, ReadingQuestion)
        .join(Session, UserResponse.session_id == Session.id)
        .outerjoin(ReadingQuestion, UserResponse.reading_question_id == ReadingQuestion.id)
        .where(
            and_(
                Session.user_id == user_id,
                Session.skill == "reading",
                Session.started_at >= since,
            )
        )
        .order_by(UserResponse.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    if not rows:
        return SkillErrorSummary(skill="reading")
    
    # Aggregate
    total_correct = 0
    total_errors = 0
    pattern_counts: dict[tuple[str, str], int] = defaultdict(int)  # (question_type, error_type) -> count
    pattern_examples: dict[tuple[str, str], list[dict]] = defaultdict(list)
    question_types: dict[str, int] = defaultdict(int)  # question_type -> wrong count
    
    for user_resp, session, question in rows:
        if user_resp.is_correct:
            total_correct += 1
        else:
            total_errors += 1
            q_type = question.question_type if question else "unknown"
            e_type = user_resp.error_type or "comprehension"
            
            key = (q_type, e_type)
            pattern_counts[key] += 1
            question_types[q_type] += 1
            
            # Store recent examples (max 5 per pattern)
            if len(pattern_examples[key]) < 5:
                pattern_examples[key].append({
                    "user_answer": user_resp.user_answer,
                    "correct_answer": user_resp.correct_answer,
                    "error_analysis": user_resp.error_analysis,
                    "session_id": session.id,
                })
    
    # Build patterns
    patterns = []
    for (q_type, e_type), count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        patterns.append(ErrorPattern(
            skill="reading",
            question_type=q_type,
            error_type=e_type,
            pattern_label=_label_reading_pattern(q_type, e_type),
            count=count,
            recent_examples=pattern_examples[(q_type, e_type)],
        ))
    
    total = total_correct + total_errors
    return SkillErrorSummary(
        skill="reading",
        total_errors=total_errors,
        total_correct=total_correct,
        accuracy_rate=round(total_correct / total, 2) if total > 0 else 0.0,
        error_patterns=patterns[:10],  # Top 10
    )


async def collect_listening_errors(
    user_id: int,
    db: AsyncSession,
    since: Optional[datetime] = None,
) -> SkillErrorSummary:
    """
    Collect error patterns from listening sessions.
    Includes dictation mishearing patterns if available.
    """
    since = since or datetime.utcnow() - timedelta(days=30)
    
    stmt = (
        select(UserResponse, Session, ListeningQuestion)
        .join(Session, UserResponse.session_id == Session.id)
        .outerjoin(ListeningQuestion, UserResponse.listening_question_id == ListeningQuestion.id)
        .where(
            and_(
                Session.user_id == user_id,
                Session.skill == "listening",
                Session.started_at >= since,
            )
        )
        .order_by(UserResponse.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    if not rows:
        return SkillErrorSummary(skill="listening")
    
    total_correct = 0
    total_errors = 0
    pattern_counts: dict[tuple[str, str], int] = defaultdict(int)
    pattern_examples: dict[tuple[str, str], list[dict]] = defaultdict(list)
    mishearing_counts: dict[str, int] = defaultdict(int)  # Track phonetic confusions
    
    for user_resp, session, question in rows:
        if user_resp.is_correct:
            total_correct += 1
        else:
            total_errors += 1
            q_type = question.question_type if question else "unknown"
            e_type = user_resp.error_type or "comprehension"
            
            # Check for dictation mishearing
            if "mishear" in e_type.lower() or user_resp.error_details:
                e_type = user_resp.error_type or "dictation_mishearing"
                
                # Extract phonetic confusions from error_details
                if user_resp.error_details:
                    for confusion in user_resp.error_details.get("phonetic_confusions", []):
                        pair = confusion.get("pair", "")
                        if pair:
                            mishearing_counts[pair] += 1
            
            key = (q_type, e_type)
            pattern_counts[key] += 1
            
            if len(pattern_examples[key]) < 5:
                pattern_examples[key].append({
                    "user_answer": user_resp.user_answer,
                    "correct_answer": user_resp.correct_answer,
                    "error_details": user_resp.error_details,
                    "session_id": session.id,
                })
    
    patterns = []
    for (q_type, e_type), count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        patterns.append(ErrorPattern(
            skill="listening",
            question_type=q_type,
            error_type=e_type,
            pattern_label=_label_listening_pattern(q_type, e_type),
            count=count,
            recent_examples=pattern_examples[(q_type, e_type)],
        ))
    
    # Add mishearing patterns as separate entries if significant
    for pair, count in sorted(mishearing_counts.items(), key=lambda x: -x[1]):
        if count >= 2:  # Only include if occurred at least twice
            patterns.append(ErrorPattern(
                skill="listening",
                question_type="dictation",
                error_type="phonetic_confusion",
                pattern_label=f"Confuse {pair}",
                count=count,
                recent_examples=[],
            ))
    
    total = total_correct + total_errors
    return SkillErrorSummary(
        skill="listening",
        total_errors=total_errors,
        total_correct=total_correct,
        accuracy_rate=round(total_correct / total, 2) if total > 0 else 0.0,
        error_patterns=patterns[:10],
    )


async def collect_writing_criteria(
    user_id: int,
    db: AsyncSession,
    since: Optional[datetime] = None,
    target_band: float = 7.0,
) -> WritingFeedbackSummary:
    """
    Extract writing criteria scores from Session.feedback_data.
    Identifies weak criteria below target band.
    """
    since = since or datetime.utcnow() - timedelta(days=30)
    
    stmt = (
        select(Session)
        .where(
            and_(
                Session.user_id == user_id,
                Session.skill == "writing",
                Session.started_at >= since,
                Session.feedback_data.isnot(None),
            )
        )
    )
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    if not sessions:
        return WritingFeedbackSummary()
    
    task_response_scores = []
    coherence_scores = []
    lexical_scores = []
    grammar_scores = []
    
    for session in sessions:
        fd = session.feedback_data or {}
        
        # Handle both old and new feedback formats
        if "task_response" in fd:
            task_response_scores.append(fd.get("task_response", 0))
        if "coherence" in fd:
            coherence_scores.append(fd.get("coherence", 0))
        if "lexical" in fd or "vocabulary" in fd:
            lexical_scores.append(fd.get("lexical") or fd.get("vocabulary", 0))
        if "grammar" in fd:
            grammar_scores.append(fd.get("grammar", 0))
    
    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0.0
    
    tr_avg = avg(task_response_scores)
    coh_avg = avg(coherence_scores)
    lex_avg = avg(lexical_scores)
    gra_avg = avg(grammar_scores)
    
    # Identify weak criteria
    weak = []
    if tr_avg > 0 and tr_avg < target_band:
        weak.append("task_response")
    if coh_avg > 0 and coh_avg < target_band:
        weak.append("coherence")
    if lex_avg > 0 and lex_avg < target_band:
        weak.append("lexical_resource")
    if gra_avg > 0 and gra_avg < target_band:
        weak.append("grammar")
    
    return WritingFeedbackSummary(
        task_response_avg=tr_avg,
        coherence_avg=coh_avg,
        lexical_avg=lex_avg,
        grammar_avg=gra_avg,
        sessions_count=len(sessions),
        weak_criteria=weak,
    )


async def collect_speaking_signals(
    user_id: int,
    db: AsyncSession,
    since: Optional[datetime] = None,
    target_band: float = 7.0,
) -> SpeakingFeedbackSummary:
    """
    Extract speaking feedback from Session.feedback_data.
    Includes filler word counts and weak criteria.
    """
    since = since or datetime.utcnow() - timedelta(days=30)
    
    stmt = (
        select(Session)
        .where(
            and_(
                Session.user_id == user_id,
                Session.skill == "speaking",
                Session.started_at >= since,
                Session.feedback_data.isnot(None),
            )
        )
    )
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    if not sessions:
        return SpeakingFeedbackSummary()
    
    fluency_scores = []
    lexical_scores = []
    grammar_scores = []
    pronunciation_scores = []
    filler_counts = []
    
    for session in sessions:
        fd = session.feedback_data or {}
        
        if "fluency" in fd:
            fluency_scores.append(fd.get("fluency", 0))
        if "lexical" in fd:
            lexical_scores.append(fd.get("lexical", 0))
        if "grammar" in fd:
            grammar_scores.append(fd.get("grammar", 0))
        if "pronunciation" in fd:
            pronunciation_scores.append(fd.get("pronunciation", 0))
        
        # Extract filler count from mutation data if present
        if "identified_fillers" in fd:
            filler_counts.append(len(fd.get("identified_fillers", [])))
    
    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0.0
    
    fl_avg = avg(fluency_scores)
    lex_avg = avg(lexical_scores)
    gra_avg = avg(grammar_scores)
    pro_avg = avg(pronunciation_scores)
    filler_avg = avg(filler_counts) if filler_counts else 0.0
    
    # Identify weak criteria
    weak = []
    if fl_avg > 0 and fl_avg < target_band:
        weak.append("fluency")
    if lex_avg > 0 and lex_avg < target_band:
        weak.append("lexical_resource")
    if gra_avg > 0 and gra_avg < target_band:
        weak.append("grammar")
    if pro_avg > 0 and pro_avg < target_band:
        weak.append("pronunciation")
    
    return SpeakingFeedbackSummary(
        fluency_avg=fl_avg,
        lexical_avg=lex_avg,
        grammar_avg=gra_avg,
        pronunciation_avg=pro_avg,
        sessions_count=len(sessions),
        filler_count_avg=filler_avg,
        weak_criteria=weak,
    )


async def collect_grammar_mistakes(
    user_id: int,
    db: AsyncSession,
    since: Optional[datetime] = None,
) -> SkillErrorSummary:
    """
    Collect grammar mistakes from GrammarMistake table.
    Groups by skill and error_type.
    """
    since = since or datetime.utcnow() - timedelta(days=30)
    
    # Join GrammarMistake with GrammarSkill to get user's skills
    stmt = (
        select(GrammarMistake, GrammarSkill)
        .join(GrammarSkill, GrammarMistake.skill_id == GrammarSkill.id)
        .where(
            and_(
                GrammarSkill.user_id == user_id,
                GrammarMistake.created_at >= since,
            )
        )
        .order_by(GrammarMistake.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    if not rows:
        return SkillErrorSummary(skill="grammar")
    
    pattern_counts: dict[str, int] = defaultdict(str)  # skill_name -> count
    pattern_examples: dict[str, list[dict]] = defaultdict(list)
    error_type_counts: dict[str, int] = defaultdict(int)
    
    for mistake, skill in rows:
        skill_name = skill.skill_name
        pattern_counts[skill_name] = pattern_counts.get(skill_name, 0) + 1
        
        if mistake.error_type:
            error_type_counts[mistake.error_type] += 1
        
        if len(pattern_examples[skill_name]) < 5:
            pattern_examples[skill_name].append({
                "incorrect": mistake.incorrect_sentence,
                "correct": mistake.correct_sentence,
                "explanation": mistake.explanation,
                "source": mistake.source,
            })
    
    total_errors = sum(pattern_counts.values())
    
    patterns = []
    for skill_name, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        patterns.append(ErrorPattern(
            skill="grammar",
            question_type=skill_name,
            error_type="grammar_mistake",
            pattern_label=f"{skill_name} errors",
            count=count,
            recent_examples=pattern_examples[skill_name],
        ))
    
    return SkillErrorSummary(
        skill="grammar",
        total_errors=total_errors,
        total_correct=0,  # Grammar doesn't track correct usage in the same way
        accuracy_rate=0.0,
        error_patterns=patterns[:10],
    )


async def build_cross_module_profile(
    user_id: int,
    db: AsyncSession,
    since: Optional[datetime] = None,
) -> CrossModuleErrorProfile:
    """
    Build a complete cross-module error profile for a user.
    This is the main entry point for the Error DNA agent.
    """
    since = since or datetime.utcnow() - timedelta(days=30)
    
    # Get user info
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    
    target_band = float(user.target_band) if user else 7.0
    
    # Calculate days until exam
    exam_days = None
    if user and user.exam_date:
        delta = user.exam_date - datetime.utcnow().date()
        exam_days = max(0, delta.days)
    
    # Collect all skill data in parallel
    reading = await collect_reading_errors(user_id, db, since)
    listening = await collect_listening_errors(user_id, db, since)
    writing_summary = await collect_writing_criteria(user_id, db, since, target_band)
    speaking_summary = await collect_speaking_signals(user_id, db, since, target_band)
    grammar = await collect_grammar_mistakes(user_id, db, since)
    
    # Convert writing/speaking summaries to SkillErrorSummary format
    writing = SkillErrorSummary(
        skill="writing",
        total_errors=len(writing_summary.weak_criteria),
        total_correct=4 - len(writing_summary.weak_criteria),  # 4 criteria total
        accuracy_rate=(4 - len(writing_summary.weak_criteria)) / 4 if writing_summary.sessions_count > 0 else 0,
        error_patterns=[
            ErrorPattern(
                skill="writing",
                question_type=crit,
                error_type="weak_criterion",
                pattern_label=f"{_format_criterion(crit)} below target",
                count=1,
            )
            for crit in writing_summary.weak_criteria
        ],
    )
    
    speaking = SkillErrorSummary(
        skill="speaking",
        total_errors=len(speaking_summary.weak_criteria),
        total_correct=4 - len(speaking_summary.weak_criteria),
        accuracy_rate=(4 - len(speaking_summary.weak_criteria)) / 4 if speaking_summary.sessions_count > 0 else 0,
        error_patterns=[
            ErrorPattern(
                skill="speaking",
                question_type=crit,
                error_type="weak_criterion",
                pattern_label=f"{_format_criterion(crit)} below target",
                count=1,
            )
            for crit in speaking_summary.weak_criteria
        ],
    )
    
    # Identify weakest and strongest skills
    skill_rates = {
        "reading": reading.accuracy_rate,
        "listening": listening.accuracy_rate,
        "writing": writing.accuracy_rate,
        "speaking": speaking.accuracy_rate,
        "grammar": grammar.accuracy_rate if grammar.total_errors > 0 else 1.0,
    }
    
    # Filter out skills with no data
    active_skills = {k: v for k, v in skill_rates.items() if v > 0 or k in ["reading", "listening"]}
    
    weakest = min(active_skills, key=active_skills.get) if active_skills else None
    strongest = max(active_skills, key=active_skills.get) if active_skills else None
    
    # Aggregate top patterns across all skills
    all_patterns = (
        reading.error_patterns +
        listening.error_patterns +
        writing.error_patterns +
        speaking.error_patterns +
        grammar.error_patterns
    )
    top_patterns = sorted(all_patterns, key=lambda p: -p.count)[:5]
    
    return CrossModuleErrorProfile(
        user_id=user_id,
        period_start=since,
        period_end=datetime.utcnow(),
        reading=reading,
        listening=listening,
        writing=writing,
        speaking=speaking,
        grammar=grammar,
        top_error_patterns=top_patterns,
        weakest_skill=weakest,
        strongest_skill=strongest,
        target_band=target_band,
        exam_date_days_remaining=exam_days,
    )


# ─────────────────────────────────────────────
#  Helper Functions
# ─────────────────────────────────────────────

def _label_reading_pattern(question_type: str, error_type: str) -> str:
    """Generate human-readable pattern label for reading errors."""
    labels = {
        ("TRUE_FALSE_NOT_GIVEN", "comprehension"): "T/F/NG comprehension misses",
        ("TRUE_FALSE_NOT_GIVEN", "negative_qualifier"): "T/F/NG negative qualifier traps",
        ("TRUE_FALSE_NOT_GIVEN", "paraphrase"): "T/F/NG paraphrase confusion",
        ("MATCHING_HEADINGS", "comprehension"): "Matching headings misalignment",
        ("MATCHING_HEADINGS", "detail_trap"): "Matching headings detail traps",
        ("MULTIPLE_CHOICE", "comprehension"): "Multiple choice comprehension",
        ("MULTIPLE_CHOICE", "distractor"): "Multiple choice distractor traps",
        ("SUMMARY_COMPLETION", "vocabulary"): "Summary completion vocabulary gaps",
        ("SHORT_ANSWER", "spelling"): "Short answer spelling errors",
    }
    return labels.get((question_type, error_type), f"{question_type} {error_type}")


def _label_listening_pattern(question_type: str, error_type: str) -> str:
    """Generate human-readable pattern label for listening errors."""
    labels = {
        ("fill_blank", "dictation_mishearing"): "Dictation mishearing",
        ("fill_blank", "spelling"): "Spelling errors in dictation",
        ("multiple_choice", "distractor"): "Multiple choice distractor traps",
        ("matching", "comprehension"): "Matching comprehension",
    }
    return labels.get((question_type, error_type), f"{question_type} {error_type}")


def _format_criterion(criterion: str) -> str:
    """Format criterion name for display."""
    mapping = {
        "task_response": "Task Response",
        "coherence": "Coherence & Cohesion",
        "lexical_resource": "Lexical Resource",
        "grammar": "Grammar",
        "fluency": "Fluency",
        "pronunciation": "Pronunciation",
    }
    return mapping.get(criterion, criterion.replace("_", " ").title())


# ─────────────────────────────────────────────
#  Conversion to SkillTelemetrySummary
# ─────────────────────────────────────────────

def to_skill_telemetry(profile: CrossModuleErrorProfile) -> dict:
    """
    Convert CrossModuleErrorProfile to SkillTelemetrySummary dict
    for compatibility with SyllabusCuratorAgent.
    """
    return {
        "reading_band": _estimate_band(profile.reading.accuracy_rate),
        "reading_sessions": profile.reading.total_errors + profile.reading.total_correct,
        "reading_wrong_question_types": [p.question_type for p in profile.reading.error_patterns[:3]],
        "reading_avg_time_per_question_ms": profile.reading.avg_time_per_question_ms or 0,
        "reading_low_confidence_wins": 0,  # Would need additional tracking
        "reading_passage_friction_avg": 0,  # From telemetry
        
        "writing_band": _estimate_band(profile.writing.accuracy_rate),
        "writing_sessions": getattr(profile.writing, 'sessions_count', 0),
        "writing_weak_criteria": [p.question_type for p in profile.writing.error_patterns],
        
        "listening_band": _estimate_band(profile.listening.accuracy_rate),
        "listening_sessions": profile.listening.total_errors + profile.listening.total_correct,
        "listening_avg_seek_count": 0,  # From telemetry
        
        "speaking_band": _estimate_band(profile.speaking.accuracy_rate),
        "speaking_sessions": getattr(profile.speaking, 'sessions_count', 0),
        "speaking_filler_count_avg": 0,  # From speaking feedback
        
        "target_band": profile.target_band,
        "exam_date_days_remaining": profile.exam_date_days_remaining,
    }


def _estimate_band(accuracy_rate: float) -> float:
    """Rough band estimate from accuracy rate."""
    if accuracy_rate >= 0.9:
        return 8.0
    elif accuracy_rate >= 0.8:
        return 7.5
    elif accuracy_rate >= 0.7:
        return 7.0
    elif accuracy_rate >= 0.6:
        return 6.5
    elif accuracy_rate >= 0.5:
        return 6.0
    elif accuracy_rate >= 0.4:
        return 5.5
    else:
        return 5.0
