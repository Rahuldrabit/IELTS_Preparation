"""
LLM Provider Module - Modular AI model access.

This module provides a unified interface for accessing different LLM providers.
Import get_llm_client() from here instead of the legacy gemma_client.

Usage:
    from services.llm import get_llm_client
    
    client = get_llm_client()  # Returns the configured provider
    response = client.generate_text("Your prompt here")
"""

from services.llm.provider import (
    get_llm_client,
    get_llm_client_for_task,
    LLMClient,
    LLMClientError,
)

__all__ = [
    "get_llm_client",
    "get_llm_client_for_task",
    "LLMClient",
    "LLMClientError",
]
