"""
OpenRouter Provider - Cloud LLM provider with access to many models.

Uses the OpenAI-compatible API at https://openrouter.ai/api/v1
Requires OPENROUTER_API_KEY to be set.
"""
import json
import logging
from typing import Optional, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from shared import settings
from services.llm.provider import LLMClient, LLMClientError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMClient):
    """
    Client for OpenRouter — routes to cloud models (GPT-4o, Claude, Gemma, etc.)
    via a single API key and OpenAI-compatible interface.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        api_key = settings.openrouter_api_key
        if not api_key or api_key == "":
            raise LLMClientError("OPENROUTER_API_KEY is not configured")

        self._client = OpenAI(
            base_url=self.BASE_URL,
            api_key=api_key,
        )
        self._model = settings.openrouter_model
        self._max_tokens = settings.openrouter_max_tokens

    @property
    def provider_name(self) -> str:
        return "openrouter"
    
    @property
    def model_name(self) -> str:
        return self._model

    @property
    def model(self) -> str:
        """Backward compat property."""
        return self._model

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        image_path: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured JSON output matching the given Pydantic schema."""
        try:
            schema_json = json.dumps(schema.model_json_schema(), indent=2)
            system_msg = (
                "You are a helpful AI assistant. Respond ONLY with valid JSON "
                f"matching this exact schema:\n{schema_json}\n\n"
                "No commentary, no markdown fences, just the raw JSON object."
            )

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ]

            # Note: image_path not supported in this implementation
            # Vision models would need different message format
            if image_path:
                logger.warning("OpenRouter provider does not support image input in this version")

            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=self._max_tokens,
                response_format={"type": "json_object"},
                extra_headers={
                    "HTTP-Referer": "https://ielts-tutor.app",
                    "X-Title": "IELTS AI Tutor",
                },
            )

            raw_text = response.choices[0].message.content or "{}"

            # Strip potential markdown fencing
            text = raw_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            return schema.model_validate(data)

        except json.JSONDecodeError as e:
            raise LLMClientError(f"OpenRouter output not valid JSON: {e}")
        except Exception as e:
            raise LLMClientError(f"OpenRouter call failed: {e}")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate plain text output."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=self._max_tokens,
                extra_headers={
                    "HTTP-Referer": "https://ielts-tutor.app",
                    "X-Title": "IELTS AI Tutor",
                },
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            raise LLMClientError(f"OpenRouter text generation failed: {e}")

    def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        """OpenRouter does not support audio transcription directly."""
        raise LLMClientError(
            "OpenRouter provider does not support audio transcription. "
            "Use the Google provider with GEMINI_API_KEY for audio support."
        )

    def health_check(self) -> dict:
        """Verify connection is working."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "Say 'OK' if you can read this."}],
                max_tokens=10,
                temperature=0.0,
                extra_headers={
                    "HTTP-Referer": "https://ielts-tutor.app",
                    "X-Title": "IELTS AI Tutor",
                },
            )
            text = response.choices[0].message.content or ""
            return {
                "provider": "openrouter",
                "model": self._model,
                "status": "ok" if text.strip() else "error",
                "response_preview": text[:50],
            }
        except Exception as e:
            return {
                "provider": "openrouter",
                "model": self._model,
                "status": "error",
                "error": str(e),
            }
