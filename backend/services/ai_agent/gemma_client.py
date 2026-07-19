"""
Backward Compatibility Layer for GemmaClient.

DEPRECATED: Import from services.llm instead:
    from services.llm import get_llm_client, LLMClientError

This module is retained for backward compatibility with existing code.
It delegates to the new modular provider system in services.llm.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import the new provider system's compatibility layer
from services.llm.provider import (
    get_gemma_client,
    GemmaClientError,
    LLMClient,
)

# Re-export for backward compatibility
# All existing imports continue to work unchanged

__all__ = [
    "get_gemma_client",
    "GemmaClient",
    "GemmaClientError",
]

# Create alias for backward compatibility
GemmaClient = type(get_gemma_client())

logger.info(
    "gemma_client.py is deprecated. "
    "New code should import from services.llm instead: "
    "from services.llm import get_llm_client"
)
