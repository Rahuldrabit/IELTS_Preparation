"""
Mock test question utilities.

Consolidates the objective-question traversal logic for listening and reading
sections that was previously duplicated in main.py and evaluator.py.
"""
from typing import Any, Dict, Iterator, Tuple

from shared.answer_utils import normalize_answer


def iter_objective_questions(
    section_type: str,
    content_data: dict,
) -> Iterator[Tuple[int, str, str, str]]:
    """
    Iterate over objective questions in listening or reading content.
    
    Normalizes the different content structures between listening (sections)
    and reading (passages) to yield a consistent question stream.
    
    Args:
        section_type: "listening" or "reading"
        content_data: The section's content_data dict from MockTestSection
        
    Yields:
        Tuples of (question_id, question_type, user_answer_key, correct_answer)
        where user_answer_key is the key to look up in the answers dict
    """
    if not content_data:
        return
    
    if section_type == "listening":
        sections = content_data.get("sections", [])
        for item in sections:
            for q in item.get("questions", []):
                qid = q.get("id")
                qtype = q.get("type", "UNKNOWN")
                correct = q.get("correct_answer", "")
                if qid is not None:
                    yield qid, qtype, str(qid), correct
    
    elif section_type == "reading":
        passages = content_data.get("passages", [])
        for passage in passages:
            for q in passage.get("questions", []):
                qid = q.get("id")
                qtype = q.get("type", "UNKNOWN")
                correct = q.get("correct_answer", "")
                if qid is not None:
                    yield qid, qtype, str(qid), correct


def score_objective_section(
    section_type: str,
    content_data: dict,
    user_answers: dict,
) -> dict:
    """
    Score an objective section (listening or reading) by comparing answers.
    
    Args:
        section_type: "listening" or "reading"
        content_data: The section's content_data dict
        user_answers: Dict of question_id -> user_answer
        
    Returns:
        Dict with score, band_estimate, correct, total, and question_type_breakdown
    """
    correct_count = 0
    total_questions = 0
    type_stats: Dict[str, dict] = {}
    
    for qid, qtype, answer_key, correct in iter_objective_questions(section_type, content_data):
        total_questions += 1
        
        # Track per-question-type stats
        if qtype not in type_stats:
            type_stats[qtype] = {"correct": 0, "total": 0}
        type_stats[qtype]["total"] += 1
        
        # Compare answers using shared normalization
        user_answer = user_answers.get(answer_key, "")
        if normalize_answer(user_answer) == normalize_answer(correct):
            correct_count += 1
            type_stats[qtype]["correct"] += 1
    
    if total_questions == 0:
        return {"score": 0, "band_estimate": 0, "correct": 0, "total": 0, "type_breakdown": []}
    
    score_pct = (correct_count / total_questions) * 100
    band_estimate = _score_to_band(correct_count, total_questions)
    
    # Build type breakdown
    type_breakdown = [
        {
            "question_type": qtype,
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy_percent": round((stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1),
        }
        for qtype, stats in sorted(type_stats.items())
    ]
    
    return {
        "score": round(score_pct, 1),
        "band_estimate": band_estimate,
        "correct": correct_count,
        "total": total_questions,
        "type_breakdown": type_breakdown,
    }


def _score_to_band(correct: int, total: int) -> float:
    """
    Convert raw score to IELTS band estimate.
    Uses approximate IELTS band conversion (40 questions scale).
    """
    if total == 0:
        return 0.0
    
    # Normalize to 40-question scale
    normalized = (correct / total) * 40
    
    # IELTS approximate band conversion table (Academic)
    if normalized >= 39:
        return 9.0
    elif normalized >= 37:
        return 8.5
    elif normalized >= 35:
        return 8.0
    elif normalized >= 33:
        return 7.5
    elif normalized >= 30:
        return 7.0
    elif normalized >= 27:
        return 6.5
    elif normalized >= 23:
        return 6.0
    elif normalized >= 19:
        return 5.5
    elif normalized >= 15:
        return 5.0
    elif normalized >= 12:
        return 4.5
    elif normalized >= 9:
        return 4.0
    elif normalized >= 6:
        return 3.5
    else:
        return 3.0
