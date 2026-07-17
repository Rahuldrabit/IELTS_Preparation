"""
Unified AI Client — routes to the best available provider with automatic fallback.

Priority order:
  1. OpenRouter (cloud) — if OPENROUTER_API_KEY is set
  2. Google AI SDK (cloud) — if GEMINI_API_KEY is set
  3. LM Studio (local) — fallback to local inference

The client tries providers in order and falls through on initialization failure.
At call time, if the active provider fails, it does NOT auto-fallback (to keep
latency predictable). Switch providers by restarting with correct env vars.

This module remains the single entry point — all services import from here.
"""
import json
import logging
import os
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from shared import settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class GemmaClientError(Exception):
    """Raised when AI API call fails (kept for backward compat)."""
    pass


class GemmaClient:
    """
    Unified AI client that delegates to the best available provider.
    Providers are tried at init time in priority order.
    """

    def __init__(self):
        self._provider = None
        self._provider_name: str = "none"

        # --- Priority 1: OpenRouter ---
        if self._try_openrouter():
            return

        # --- Priority 2: Google AI SDK ---
        if self._try_google():
            return

        # --- Priority 3: LM Studio (local) ---
        if self._try_lmstudio():
            return

        logger.error("No AI provider available. Set OPENROUTER_API_KEY, GEMINI_API_KEY, or run LM Studio.")

    def _try_openrouter(self) -> bool:
        """Attempt to initialize OpenRouter client."""
        api_key = settings.openrouter_api_key
        if not api_key or api_key == "":
            return False
        try:
            from services.ai_agent.openrouter_client import OpenRouterClient
            self._provider = OpenRouterClient()
            self._provider_name = "openrouter"
            logger.info(f"[AI] Using OpenRouter — model: {self._provider.model}")
            return True
        except Exception as e:
            logger.warning(f"[AI] OpenRouter init failed: {e}")
            return False

    def _try_google(self) -> bool:
        """Attempt to initialize Google AI SDK client."""
        api_key = settings.gemini_api_key
        if not api_key or api_key == "" or api_key == "your-gemini-api-key-here":
            return False
        try:
            from google import genai
            self._google_client = genai.Client(api_key=api_key)
            self._google_model = settings.gemma_model
            self._provider_name = "google"
            logger.info(f"[AI] Using Google AI SDK — model: {self._google_model}")
            return True
        except ImportError:
            logger.warning("[AI] google-genai package not installed, skipping Google provider.")
            return False
        except Exception as e:
            logger.warning(f"[AI] Google AI init failed: {e}")
            return False

    def _try_lmstudio(self) -> bool:
        """Attempt to initialize LM Studio client."""
        try:
            from services.ai_agent.lmstudio_client import LMStudioClient
            client = LMStudioClient()
            # Quick connectivity check (non-blocking, just verifies the server responds)
            health = client.health_check()
            if health["status"] == "ok":
                self._provider = client
                self._provider_name = "lmstudio"
                logger.info(f"[AI] Using LM Studio — model: {client.model}")
                return True
            else:
                logger.warning(f"[AI] LM Studio not responding: {health.get('error', 'unknown')}")
                return False
        except Exception as e:
            logger.warning(f"[AI] LM Studio init failed: {e}")
            return False

    @property
    def mode(self) -> str:
        return self._provider_name

    # ─────────────────────────────────────────────
    #  Public API (backward-compatible)
    # ─────────────────────────────────────────────

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        image_path: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output matching the given Pydantic schema."""
        if self._provider_name == "google":
            return self._google_structured(prompt, schema, image_path, temperature)
        elif self._provider is not None:
            # OpenRouter or LMStudio — both have .generate_structured()
            try:
                return self._provider.generate_structured(prompt, schema, temperature)
            except Exception as e:
                raise GemmaClientError(str(e))
        else:
            raise GemmaClientError("No AI provider available. Configure OPENROUTER_API_KEY or start LM Studio.")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate plain text output."""
        if self._provider_name == "google":
            return self._google_text(prompt, system_prompt, temperature)
        elif self._provider is not None:
            try:
                return self._provider.generate_text(prompt, system_prompt, temperature)
            except Exception as e:
                raise GemmaClientError(str(e))
        else:
            raise GemmaClientError("No AI provider available. Configure OPENROUTER_API_KEY or start LM Studio.")

    def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe audio file. Only supported in Google mode."""
        if self._provider_name == "google":
            return self._google_transcribe(audio_path, prompt)
        else:
            return "[Audio transcription requires Google AI SDK with GEMINI_API_KEY]"

    def health_check(self) -> dict:
        """Verify connection is working."""
        if self._provider_name == "google":
            try:
                from google.genai import types
                response = self._google_client.models.generate_content(
                    model=self._google_model,
                    contents="Say 'OK' if you can read this.",
                )
                return {
                    "provider": "google",
                    "model": self._google_model,
                    "status": "ok" if response.text else "error",
                    "response_preview": (response.text or "")[:50],
                }
            except Exception as e:
                return {
                    "provider": "google",
                    "model": self._google_model,
                    "status": "error",
                    "error": str(e),
                }
        elif self._provider is not None:
            return self._provider.health_check()
        else:
            return {
                "provider": "none",
                "model": "N/A",
                "status": "error",
                "error": "No AI provider configured",
            }

    # ─────────────────────────────────────────────
    #  Google AI SDK implementation (kept inline since it needs image support)
    # ─────────────────────────────────────────────

    def _google_structured(
        self, prompt: str, schema: Type[T], image_path: Optional[str], temperature: float
    ) -> T:
        from google.genai import types
        from PIL import Image

        try:
            contents = []
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                contents.append(img)
            contents.append(prompt)

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=temperature,
            )

            response = self._google_client.models.generate_content(
                model=self._google_model,
                contents=contents,
                config=config,
            )

            raw_text = response.text
            data = json.loads(raw_text) if isinstance(raw_text, str) else raw_text
            return schema.model_validate(data)

        except json.JSONDecodeError as e:
            raise GemmaClientError(f"Failed to parse Google AI output as JSON: {e}")
        except Exception as e:
            raise GemmaClientError(f"Google AI call failed: {e}")

    def _google_text(self, prompt: str, system_prompt: Optional[str], temperature: float) -> str:
        from google.genai import types
        try:
            contents = []
            if system_prompt:
                contents.append(f"System: {system_prompt}\n\n")
            contents.append(prompt)

            config = types.GenerateContentConfig(temperature=temperature)
            response = self._google_client.models.generate_content(
                model=self._google_model,
                contents="".join(contents),
                config=config,
            )
            return response.text or ""
        except Exception as e:
            raise GemmaClientError(f"Google text generation failed: {e}")

    def _google_transcribe(self, audio_path: str, prompt: Optional[str]) -> str:
        try:
            audio_file = self._google_client.files.upload(file=audio_path)
            contents = []
            if prompt:
                contents.append(prompt)
            contents.append(audio_file)

            response = self._google_client.models.generate_content(
                model=self._google_model,
                contents=contents,
            )
            return response.text or ""
        except Exception as e:
            raise GemmaClientError(f"Audio transcription failed: {e}")


# ─────────────────────────────────────────────
#  Singleton (lazy-initialized)
# ─────────────────────────────────────────────

_gemma_client: Optional[GemmaClient] = None


def get_gemma_client() -> GemmaClient:
    """Get or create the singleton GemmaClient instance."""
    global _gemma_client
    if _gemma_client is None:
        _gemma_client = GemmaClient()
    return _gemma_client
