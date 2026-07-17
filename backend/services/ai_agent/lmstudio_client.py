"""
LM Studio Client — local LLM inference via OpenAI-compatible API.

Connects to LM Studio's local server (default: http://host.docker.internal:1234/v1).
No API key required (uses a dummy key).
"""
import json
import logging
from typing import Optional, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from shared import settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class LMStudioClientError(Exception):
    """Raised when LM Studio API call fails."""
    pass


class LMStudioClient:
    """
    Client for LM Studio — local inference server with OpenAI-compatible API.
    Useful for offline development and privacy-sensitive workloads.
    """

    def __init__(self):
        self._client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,  # "lm-studio" dummy key
        )
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens

    @property
    def model(self) -> str:
        return self._model

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        temperature: float = 0.0,
    ) -> T:
        """
        Generate structured JSON output matching the given Pydantic schema.
        Uses json_schema response format supported by LM Studio.
        """
        try:
            schema_json = json.dumps(schema.model_json_schema(), indent=2)
            system_msg = (
                "You are a helpful AI assistant. Respond ONLY with valid JSON "
                f"matching this exact schema:\n{schema_json}\n\n"
                "No commentary, no markdown, just the raw JSON object."
            )

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema.model_json_schema(),
                    },
                },
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
            raise LMStudioClientError(f"LM Studio output not valid JSON: {e}")
        except Exception as e:
            raise LMStudioClientError(f"LM Studio call failed: {e}")

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
            raise LMStudioClientError(f"LM Studio text generation failed: {e}")

    def health_check(self) -> dict:
        """Verify connection is working."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "Say 'OK' if you can read this."}],
                max_tokens=50,
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
