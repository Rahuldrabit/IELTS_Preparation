"""
BaseAgent — shared foundation for all IELTS AI agents.

Every agent inherits from this class. It provides:
  - Lazy access to the GemmaClient singleton (no coupling to init order)
  - run_structured()   — async wrapper around generate_structured()
  - run_text()         — async wrapper around generate_text()
  - run_transcribe()   — async wrapper around transcribe_audio()
  - Consistent error logging with the agent's name

Engineering principle: each agent is a stateless callable.
Pass input → get output. No shared mutable state between agents.
"""
import asyncio
import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from services.llm import LLMClientError, get_llm_client
from services.llm.provider import LLMClient

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Stateless base class for all IELTS AI agents.

    Subclasses must set:
        name: str        — human-readable agent name, used in logs + registry
        description: str — one-sentence description of what this agent does

    All LLM calls go through the shared LLMClient singleton.
    Heavy sync SDK calls are offloaded to a thread pool via run_in_executor
    so they never block the asyncio event loop.
    """

    name: str = "BaseAgent"
    description: str = "Abstract base — do not use directly"

    # ─────────────────────────────────────────────
    #  Internal helpers
    # ─────────────────────────────────────────────

    @property
    def client(self) -> LLMClient:
        """Lazy access to the shared LLMClient singleton."""
        return get_llm_client()

    async def run_structured(
        self,
        prompt: str,
        schema: Type[T],
        temperature: float = 0.1,
        image_path: Optional[str] = None,
    ) -> T:
        """
        Async wrapper: calls generate_structured() in a thread pool.
        Returns a validated Pydantic instance of `schema`.
        Raises GemmaClientError on failure.
        """
        loop = asyncio.get_event_loop()
        try:
            result: T = await loop.run_in_executor(
                None,
                lambda: self.client.generate_structured(
                    prompt=prompt,
                    schema=schema,
                    temperature=temperature,
                    image_path=image_path,
                ),
            )
            logger.debug("[%s] run_structured OK (schema=%s)", self.name, schema.__name__)
            return result
        except LLMClientError as e:
            logger.error("[%s] run_structured FAILED: %s", self.name, e)
            raise
        except Exception as e:
            logger.error("[%s] run_structured unexpected error: %s", self.name, e)
            raise LLMClientError(f"[{self.name}] {e}") from e

    async def run_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """
        Async wrapper: calls generate_text() in a thread pool.
        Returns a plain string.
        """
        loop = asyncio.get_event_loop()
        try:
            result: str = await loop.run_in_executor(
                None,
                lambda: self.client.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                ),
            )
            logger.debug("[%s] run_text OK", self.name)
            return result
        except LLMClientError as e:
            logger.error("[%s] run_text FAILED: %s", self.name, e)
            raise
        except Exception as e:
            logger.error("[%s] run_text unexpected error: %s", self.name, e)
            raise LLMClientError(f"[{self.name}] {e}") from e

    async def run_transcribe(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        """
        Async wrapper: calls transcribe_audio() in a thread pool.
        Returns the transcription string.
        """
        loop = asyncio.get_event_loop()
        try:
            result: str = await loop.run_in_executor(
                None,
                lambda: self.client.transcribe_audio(
                    audio_path=audio_path,
                    prompt=prompt,
                ),
            )
            logger.debug("[%s] run_transcribe OK", self.name)
            return result
        except LLMClientError as e:
            logger.error("[%s] run_transcribe FAILED: %s", self.name, e)
            raise
        except Exception as e:
            logger.error("[%s] run_transcribe unexpected error: %s", self.name, e)
            raise LLMClientError(f"[{self.name}] {e}") from e
