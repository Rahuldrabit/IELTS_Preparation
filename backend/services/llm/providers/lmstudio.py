"""
LM Studio Provider - Local inference via LM Studio.

LM Studio provides an OpenAI-compatible API at localhost:1234.
No API key required, but LM Studio must be running locally.
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


class LMStudioProvider(LLMClient):
    """
    Client for LM Studio — local LLM inference with OpenAI-compatible API.
    
    No API key required. Just run LM Studio and load a model.
    Default endpoint: http://localhost:1234/v1
    """

    BASE_URL = "http://localhost:1234/v1"

    def __init__(self):
        self._client = OpenAI(
            base_url=self.BASE_URL,
            api_key="lm-studio",  # LM Studio doesn't require a real key
        )
        self._model = settings.lmstudio_model
        self._max_tokens = settings.lmstudio_max_tokens

    @property
    def provider_name(self) -> str:
        return "lmstudio"
    
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

            # Note: image_path not supported in this implementation
            if image_path:
                logger.warning("LM Studio provider does not support image input in this version")

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=self._max_tokens,
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
            raise LLMClientError(f"LM Studio output not valid JSON: {e}")
        except Exception as e:
            raise LLMClientError(f"LM Studio call failed: {e}")

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
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            raise LLMClientError(f"LM Studio text generation failed: {e}")

    def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        """LM Studio does not support audio transcription."""
        raise LLMClientError(
            "LM Studio provider does not support audio transcription. "
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
            )
            text = response.choices[0].message.content or ""
            return {
                "provider": "lmstudio",
                "model": self._model,
                "status": "ok" if text.strip() else "error",
                "response_preview": text[:50],
            }
        except Exception as e:
            return {
                "provider": "lmstudio",
                "model": self._model,
                "status": "error",
                "error": str(e),
            }
