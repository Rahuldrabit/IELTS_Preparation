"""
Shared answer normalization and comparison utilities.

Provides consistent answer handling across reading, listening, mock tests,
and grammar exercises.
"""


def normalize_answer(value) -> str:
    """
    Normalize an answer value for comparison.
    
    Converts to string, strips whitespace, and lowercases.
    This matches the existing behavior across most endpoints.
    
    Args:
        value: Any value (string, number, None, etc.)
        
    Returns:
        Normalized string for comparison
    """
    if value is None:
        return ""
    return str(value).strip().lower()


def answers_match(user_answer, correct_answer) -> bool:
    """
    Check if a user's answer matches the correct answer.
    
    Uses case-insensitive comparison after normalizing both values.
    This consolidates the repeated pattern across:
    - Reading submission endpoints
    - Listening submission
    - Mock test scoring
    - Grammar exercise scoring
    
    Args:
        user_answer: The user's submitted answer
        correct_answer: The expected correct answer
        
    Returns:
        True if answers match after normalization
    """
    return normalize_answer(user_answer) == normalize_answer(correct_answer)


def normalize_answer_strict(value) -> str:
    """
    Normalize an answer with stricter rules (future use).
    
    In addition to basic normalization:
    - Removes common punctuation variations
    - Normalizes whitespace
    
    Args:
        value: Any value to normalize
        
    Returns:
        Strictly normalized string
    """
    if value is None:
        return ""
    
    result = str(value).strip().lower()
    
    # Normalize common punctuation
    result = result.replace('"', "'")  # Quote normalization
    result = result.replace("—", "-")  # Dash normalization
    result = result.replace("–", "-")
    
    # Collapse multiple spaces
    while "  " in result:
        result = result.replace("  ", " ")
    
    return result
