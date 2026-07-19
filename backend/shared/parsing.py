"""
Shared JSON parsing utilities for AI responses.

Provides robust extraction of JSON from LLM outputs that may include
markdown fences, commentary, or other non-JSON content.
"""
import json
import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def parse_json_from_response(response: str) -> Optional[dict]:
    """
    Extract JSON from an AI response that may contain extra content.
    
    Tries multiple strategies in order:
    1. Direct JSON parse
    2. Extract from markdown code fences (```json ... ```)
    3. Find first { and last } for embedded JSON
    
    Args:
        response: Raw AI response text
        
    Returns:
        Parsed dict if successful, None otherwise
    """
    if not response:
        return None
    
    # Strategy 1: Direct parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code fence
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            try:
                return json.loads(response[start:end].strip())
            except json.JSONDecodeError:
                pass
    
    # Strategy 3: Find first { and last }
    if "{" in response:
        start = response.find("{")
        end = response.rfind("}") + 1
        if end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass
    
    return None


def parse_json_to_model(response: str, schema: Type[T]) -> Optional[T]:
    """
    Parse JSON from AI response and validate against a Pydantic model.
    
    Args:
        response: Raw AI response text
        schema: Pydantic model class to validate against
        
    Returns:
        Validated model instance if successful, None otherwise
    """
    data = parse_json_from_response(response)
    if data is None:
        return None
    
    try:
        return schema.model_validate(data)
    except Exception as e:
        logger.warning("Failed to validate JSON to %s: %s", schema.__name__, e)
        return None


def extract_json_value(response: str, key: str, default=None):
    """
    Extract a single value from JSON in an AI response.
    
    Args:
        response: Raw AI response text
        key: Dictionary key to extract
        default: Default value if key not found
        
    Returns:
        Value for key if found, else default
    """
    data = parse_json_from_response(response)
    if data is None:
        return default
    return data.get(key, default)
