"""
Shared utilities for mapping generated exam questions to ORM models
and building frontend-safe responses.

Consolidates the common patterns between reading and listening services.
"""
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from shared.schemas import (
    ExamOutput,
    QuestionGroup,
    QuestionItem,
    QuestionGroupPublic,
    QuestionItemPublic,
)


# ─────────────────────────────────────────────
#  Generated Question Iteration
# ─────────────────────────────────────────────

def iter_generated_questions(exam: ExamOutput) -> Iterator[Tuple[QuestionGroup, QuestionItem]]:
    """
    Iterate over all questions in an ExamOutput with their group context.
    
    Yields tuples of (QuestionGroup, QuestionItem) for each question,
    preserving the group context needed for question_type and group_id.
    
    Args:
        exam: ExamOutput from AI generation
        
    Yields:
        Tuples of (group, question) for each question
    """
    for group in exam.question_groups:
        for question in group.questions:
            yield group, question


# ─────────────────────────────────────────────
#  Question Field Mapping
# ─────────────────────────────────────────────

def get_question_db_fields(
    group: QuestionGroup,
    question: QuestionItem,
    fk_id: int,
    fk_field: str = "passage_id",
) -> Dict[str, Any]:
    """
    Extract common DB fields from a generated question.
    
    Returns a dict suitable for passing to an ORM constructor.
    Foreign key field name is configurable (passage_id, section_id, etc.)
    
    Args:
        group: QuestionGroup containing this question
        question: QuestionItem to extract fields from
        fk_id: Foreign key value (passage_id, section_id, etc.)
        fk_field: Name of the foreign key field (default: "passage_id")
        
    Returns:
        Dict with common question fields for ORM construction
    """
    return {
        fk_field: fk_id,
        "question_text": question.prompt_text,
        "question_type": group.question_type,
        "group_id": group.group_id,
        "question_number": question.question_number,
        "options": question.local_options,
        "correct_answer": question.backend_evaluation.correct_answer,
        "explanation": question.backend_evaluation.evidence_text,
        "question_evaluation": question.backend_evaluation.model_dump(),
    }


# ─────────────────────────────────────────────
#  Frontend-Safe Response Building
# ─────────────────────────────────────────────

# Default instructions for common question types
DEFAULT_INSTRUCTIONS = {
    # Reading types
    "TRUE_FALSE_NOT_GIVEN": "Do the following statements agree with the information given in the passage? Write TRUE if the statement agrees with the information, FALSE if the statement contradicts the information, or NOT GIVEN if there is no information on this.",
    "MATCHING_HEADINGS": "The passage has paragraphs labeled A-G. Which paragraph contains the following information? Write the correct letter, A-G.",
    "SUMMARY_COMPLETION": "Complete the summary below. Choose ONE WORD ONLY from the passage for each answer.",
    "MULTIPLE_CHOICE": "Choose the correct answer, A, B, C or D.",
    "SENTENCE_COMPLETION": "Complete each sentence with the correct ending, A-G, below.",
    # Listening types
    "FILL_BLANK": "Complete the notes below. Write ONE WORD AND/OR A NUMBER for each answer.",
    "MATCHING_INFORMATION": "Match each statement with the correct speaker. Write A, B or C.",
}


def build_question_item_public(
    question_id: int,
    question_number: int,
    prompt_text: str,
    question_type: str,
    options: Optional[List[str]] = None,
    question_evaluation: Optional[Dict[str, Any]] = None,
) -> QuestionItemPublic:
    """
    Build a frontend-safe QuestionItemPublic.
    
    IMPORTANT: This function ensures we NEVER expose correct_answer or
    other hidden evaluation data. If question_evaluation is provided,
    it will be filtered to only include safe metadata (e.g., trap_type
    for adversarial questions).
    
    Args:
        question_id: Database ID of the question
        question_number: Question number (1-indexed)
        prompt_text: The question text
        question_type: Question type (TRUE_FALSE_NOT_GIVEN, etc.)
        options: Optional list of answer options
        question_evaluation: Optional evaluation dict (will be filtered!)
        
    Returns:
        QuestionItemPublic safe for frontend response
    """
    # Filter question_evaluation to only safe fields
    safe_evaluation = None
    if question_evaluation:
        # Only expose adversarial trap metadata, never correct_answer/evidence
        safe_keys = {"trap_type", "trap_explanation", "cognitive_distractor_analysis"}
        safe_evaluation = {
            k: v for k, v in question_evaluation.items()
            if k in safe_keys
        }
        # Don't include empty evaluation dicts
        if not safe_evaluation:
            safe_evaluation = None
    
    return QuestionItemPublic(
        id=question_id,
        question_number=question_number,
        prompt_text=prompt_text,
        local_options=options,
        question_type=question_type,
        question_evaluation=safe_evaluation,
    )


def build_question_groups_public(
    questions: List[Any],
    instructions_map: Optional[Dict[str, str]] = None,
    get_question_id: Callable[[Any], int] = lambda q: q.id,
    get_question_number: Callable[[Any], int] = lambda q: q.question_number or 0,
    get_prompt_text: Callable[[Any], str] = lambda q: q.question_text,
    get_question_type: Callable[[Any], str] = lambda q: q.question_type,
    get_options: Callable[[Any], Optional[List[str]]] = lambda q: q.options,
    get_group_id: Callable[[Any], str] = lambda q: q.group_id or "group_1",
    get_evaluation: Callable[[Any], Optional[Dict]] = lambda q: getattr(q, 'question_evaluation', None),
) -> List[QuestionGroupPublic]:
    """
    Build frontend-safe question groups from a list of DB question objects.
    
    This consolidates the repeated grouping and response-building logic
    between reading and listening services.
    
    Args:
        questions: List of ORM question objects
        instructions_map: Optional custom instructions per question type
                         (merges with DEFAULT_INSTRUCTIONS)
        get_question_id: Function to extract ID from question object
        get_question_number: Function to extract question number
        get_prompt_text: Function to extract prompt text
        get_question_type: Function to extract question type
        get_options: Function to extract options list
        get_group_id: Function to extract group ID
        get_evaluation: Function to extract question evaluation dict
        
    Returns:
        List of QuestionGroupPublic ready for API response
    """
    # Merge custom instructions with defaults
    instructions = {**DEFAULT_INSTRUCTIONS, **(instructions_map or {})}
    
    # Group questions by group_id
    questions_by_group: Dict[str, List[Any]] = {}
    for q in questions:
        group_id = get_group_id(q)
        if group_id not in questions_by_group:
            questions_by_group[group_id] = []
        questions_by_group[group_id].append(q)
    
    # Build response groups
    question_groups = []
    for group_id, group_questions in questions_by_group.items():
        # Get question type from first question
        qtype = get_question_type(group_questions[0]) if group_questions else "UNKNOWN"
        
        # Sort questions by question_number
        sorted_questions = sorted(
            group_questions,
            key=lambda q: get_question_number(q) or 0
        )
        
        # Build question items
        question_items = []
        for idx, q in enumerate(sorted_questions):
            qnum = get_question_number(q) or (idx + 1)
            question_items.append(
                build_question_item_public(
                    question_id=get_question_id(q),
                    question_number=qnum,
                    prompt_text=get_prompt_text(q),
                    question_type=qtype,
                    options=get_options(q),
                    question_evaluation=get_evaluation(q),
                )
            )
        
        question_groups.append(QuestionGroupPublic(
            group_id=group_id,
            question_type=qtype,
            instructions=instructions.get(qtype, "Answer the following questions."),
            questions=question_items,
        ))
    
    return question_groups
