"""Shared utilities and base classes for all services."""
from shared.config import settings
from shared.database import Base, get_db, get_db_session, engine
from shared import schemas  # noqa: F401 — re-export for convenience
from shared.parsing import parse_json_from_response, parse_json_to_model
from shared.answer_utils import normalize_answer, answers_match
from shared.exam_questions import (
    iter_generated_questions,
    get_question_db_fields,
    build_question_groups_public,
    build_question_item_public,
)

__all__ = [
    "settings",
    "Base",
    "get_db",
    "get_db_session",
    "engine",
    "schemas",
    "parse_json_from_response",
    "parse_json_to_model",
    "normalize_answer",
    "answers_match",
    "iter_generated_questions",
    "get_question_db_fields",
    "build_question_groups_public",
    "build_question_item_public",
]