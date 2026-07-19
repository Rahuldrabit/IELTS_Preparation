"""
LLM Provider - Central configuration for AI model access.

This module replaces the global GemmaClient singleton with a configurable
provider system. Each service can request a client appropriate for its needs.

Current default: Gemma 4 (via OpenRouter, Google AI, or LM Studio)
"""
import logging
from typing import Optional, Type, TypeVar, Dict, Any

from pydantic import BaseModel

from shared import settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when LLM API call fails."""
    pass


class LLMClient:
    """
    Base interface for LLM clients.
    
    All providers must implement these methods.
    """
    
    @property
    def provider_name(self) -> str:
        """Return the name of this provider (e.g., 'openrouter', 'google', 'lmstudio')."""
        raise NotImplementedError
    
    @property
    def model_name(self) -> str:
        """Return the model name being used."""
        raise NotImplementedError
    
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        image_path: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output matching the given Pydantic schema."""
        raise NotImplementedError
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate plain text output."""
        raise NotImplementedError
    
    def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe audio file. May not be supported by all providers."""
        raise NotImplementedError
    
    def health_check(self) -> dict:
        """Verify connection is working."""
        raise NotImplementedError


# ─────────────────────────────────────────────
#  Provider Registry
# ─────────────────────────────────────────────

# Registry of available providers (lazy-loaded)
_providers: Dict[str, LLMClient] = {}
_default_provider: Optional[str] = None


def _init_default_provider() -> Optional[LLMClient]:
    """
    Initialize the default provider based on available configuration.
    
    Priority order:
      1. OpenRouter (cloud) — if OPENROUTER_API_KEY is set
      2. Google AI SDK (cloud) — if GEMINI_API_KEY is set
      3. LM Studio (local) — fallback to local inference
    """
    global _default_provider
    
    # Try OpenRouter first
    client = _try_openrouter()
    if client:
        _default_provider = "openrouter"
        _providers["default"] = client
        _providers["openrouter"] = client
        return client
    
    # Try Google AI SDK
    client = _try_google()
    if client:
        _default_provider = "google"
        _providers["default"] = client
        _providers["google"] = client
        return client
    
    # Try LM Studio
    client = _try_lmstudio()
    if client:
        _default_provider = "lmstudio"
        _providers["default"] = client
        _providers["lmstudio"] = client
        return client
    
    logger.error("No LLM provider available. Set OPENROUTER_API_KEY, GEMINI_API_KEY, or run LM Studio.")
    return None


def _try_openrouter() -> Optional[LLMClient]:
    """Attempt to initialize OpenRouter client."""
    api_key = settings.openrouter_api_key
    if not api_key or api_key == "":
        return None
    try:
        from services.llm.providers.openrouter import OpenRouterProvider
        client = OpenRouterProvider()
        logger.info(f"[LLM] Using OpenRouter — model: {client.model_name}")
        return client
    except Exception as e:
        logger.warning(f"[LLM] OpenRouter init failed: {e}")
        return None


def _try_google() -> Optional[LLMClient]:
    """Attempt to initialize Google AI SDK client."""
    api_key = settings.gemini_api_key
    if not api_key or api_key == "" or api_key == "your-gemini-api-key-here":
        return None
    try:
        from services.llm.providers.google import GoogleProvider
        client = GoogleProvider()
        logger.info(f"[LLM] Using Google AI SDK — model: {client.model_name}")
        return client
    except ImportError:
        logger.warning("[LLM] google-genai package not installed, skipping Google provider.")
        return None
    except Exception as e:
        logger.warning(f"[LLM] Google AI init failed: {e}")
        return None


def _try_lmstudio() -> Optional[LLMClient]:
    """Attempt to initialize LM Studio client."""
    try:
        from services.llm.providers.lmstudio import LMStudioProvider
        client = LMStudioProvider()
        health = client.health_check()
        if health["status"] == "ok":
            logger.info(f"[LLM] Using LM Studio — model: {client.model_name}")
            return client
        else:
            logger.warning(f"[LLM] LM Studio not responding: {health.get('error', 'unknown')}")
            return None
    except Exception as e:
        logger.warning(f"[LLM] LM Studio init failed: {e}")
        return None


# ─────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────

def get_llm_client() -> LLMClient:
    """
    Get the default LLM client instance.
    
    Returns the first available provider in priority order:
    OpenRouter > Google AI > LM Studio
    
    Raises:
        LLMClientError: If no provider is configured
    """
    if "default" in _providers:
        return _providers["default"]
    
    client = _init_default_provider()
    if client:
        return client
    
    raise LLMClientError(
        "No LLM provider available. Configure OPENROUTER_API_KEY, GEMINI_API_KEY, "
        "or start LM Studio on localhost:1234"
    )


def get_llm_client_for_task(task: str) -> LLMClient:
    """
    Get an LLM client appropriate for a specific task.
    
    This allows future extensibility for task-specific model selection.
    Currently returns the default provider for all tasks.
    
    Args:
        task: Task identifier (e.g., 'writing_scoring', 'reading_generation', 
              'listening_transcription', 'vocabulary_enrichment')
    
    Returns:
        LLMClient instance appropriate for the task
    """
    # Future: Implement task-specific model routing
    # For now, all tasks use the default provider
    return get_llm_client()


def get_provider(name: str) -> Optional[LLMClient]:
    """
    Get a specific provider by name.
    
    Args:
        name: Provider name ('openrouter', 'google', 'lmstudio')
    
    Returns:
        LLMClient instance or None if not available
    """
    if name in _providers:
        return _providers[name]
    
    # Lazy-load specific provider
    if name == "openrouter":
        client = _try_openrouter()
    elif name == "google":
        client = _try_google()
    elif name == "lmstudio":
        client = _try_lmstudio()
    else:
        return None
    
    if client:
        _providers[name] = client
    return client


def get_available_providers() -> list[str]:
    """Return list of available provider names."""
    return list(_providers.keys())


# ─────────────────────────────────────────────
#  Backward Compatibility Layer
# ─────────────────────────────────────────────

# These maintain backward compatibility with existing code that imports
# from services.ai_agent.gemma_client. New code should use get_llm_client().

class _GemmaClientCompat(LLMClient):
    """
    Backward-compatible wrapper that delegates to the new provider system.
    
    This allows existing code to continue using get_gemma_client() while
    new code migrates to get_llm_client().
    """
    
    def __init__(self):
        self._delegate = get_llm_client()
    
    @property
    def provider_name(self) -> str:
        return self._delegate.provider_name
    
    @property
    def model_name(self) -> str:
        return self._delegate.model_name
    
    @property
    def mode(self) -> str:
        """Backward compat property."""
        return self._delegate.provider_name
    
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        image_path: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        return self._delegate.generate_structured(prompt, schema, image_path, temperature)
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        return self._delegate.generate_text(prompt, system_prompt, temperature)
    
    def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        return self._delegate.transcribe_audio(audio_path, prompt)
    
    def health_check(self) -> dict:
        return self._delegate.health_check()


# Legacy singleton for backward compatibility
_gemma_client_compat: Optional[_GemmaClientCompat] = None


def get_gemma_client() -> _GemmaClientCompat:
    """
    [DEPRECATED] Use get_llm_client() instead.
    
    This function is retained for backward compatibility.
    New code should import from services.llm instead.
    """
    global _gemma_client_compat
    if _gemma_client_compat is None:
        _gemma_client_compat = _GemmaClientCompat()
    return _gemma_client_compat


# Alias for backward compatibility
GemmaClientError = LLMClientError
