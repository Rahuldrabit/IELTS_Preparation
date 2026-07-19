"""
Google AI Provider - Direct access to Gemini models via Google AI SDK.

Requires GEMINI_API_KEY to be set.
Supports text generation, structured output, and audio transcription.
"""
import json
import logging
import os
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from shared import settings
from services.llm.provider import LLMClient, LLMClientError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class GoogleProvider(LLMClient):
    """
    Client for Google AI SDK — direct access to Gemini models.
    
    Supports:
    - Text generation
    - Structured JSON output
    - Image understanding
    - Audio transcription
    """

    def __init__(self):
        api_key = settings.gemini_api_key
        if not api_key or api_key == "" or api_key == "your-gemini-api-key-here":
            raise LLMClientError("GEMINI_API_KEY is not configured")
        
        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            self._model = settings.gemma_model  # Uses gemma_model setting for backward compat
        except ImportError:
            raise LLMClientError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )

    @property
    def provider_name(self) -> str:
        return "google"
    
    @property
    def model_name(self) -> str:
        return self._model

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        image_path: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output matching the given Pydantic schema."""
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

            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )

            raw_text = response.text
            data = json.loads(raw_text) if isinstance(raw_text, str) else raw_text
            return schema.model_validate(data)

        except json.JSONDecodeError as e:
            raise LLMClientError(f"Failed to parse Google AI output as JSON: {e}")
        except Exception as e:
            raise LLMClientError(f"Google AI call failed: {e}")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate plain text output."""
        from google.genai import types
        try:
            contents = []
            if system_prompt:
                contents.append(f"System: {system_prompt}\n\n")
            contents.append(prompt)

            config = types.GenerateContentConfig(temperature=temperature)
            response = self._client.models.generate_content(
                model=self._model,
                contents="".join(contents),
                config=config,
            )
            return response.text or ""
        except Exception as e:
            raise LLMClientError(f"Google text generation failed: {e}")

    def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe audio file using Google AI."""
        try:
            audio_file = self._client.files.upload(file=audio_path)
            contents = []
            if prompt:
                contents.append(prompt)
            contents.append(audio_file)

            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
            )
            return response.text or ""
        except Exception as e:
            raise LLMClientError(f"Audio transcription failed: {e}")

    def health_check(self) -> dict:
        """Verify connection is working."""
        try:
            from google.genai import types
            response = self._client.models.generate_content(
                model=self._model,
                contents="Say 'OK' if you can read this.",
            )
            return {
                "provider": "google",
                "model": self._model,
                "status": "ok" if response.text else "error",
                "response_preview": (response.text or "")[:50],
            }
        except Exception as e:
            return {
                "provider": "google",
                "model": self._model,
                "status": "error",
                "error": str(e),
            }
