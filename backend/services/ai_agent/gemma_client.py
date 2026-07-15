"""
Gemma 4 Client using google-genai SDK.

This is the single entry point for all structured AI generation.
Uses native structured output support (response_schema) for guaranteed JSON.
"""
import json
import os
from typing import Optional, Type, TypeVar

from PIL import Image
from pydantic import BaseModel
from google import genai
from google.genai import types

from shared import settings

T = TypeVar("T", bound=BaseModel)


class GemmaClientError(Exception):
    """Raised when Gemma 4 API call fails."""
    pass


class GemmaClient:
    """
    Wrapper around google-genai SDK for Gemma 4.

    Usage:
        client = GemmaClient()
        result = client.generate_structured(prompt, schema=ExamOutput)
        # result is an ExamOutput instance
    """

    def __init__(self):
        api_key = settings.gemini_api_key
        if not api_key:
            raise GemmaClientError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = settings.gemma_model

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        image_path: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """
        Generate structured output matching the given Pydantic schema.

        Args:
            prompt: The instruction prompt for the model.
            schema: A Pydantic BaseModel class defining the output structure.
            image_path: Optional path to an image file for VLM tasks.
            temperature: 0.0 for deterministic output (recommended for exams).

        Returns:
            An instance of the schema class populated with model output.

        Raises:
            GemmaClientError: If the API call fails or output doesn't parse.
        """
        try:
            # Build content parts
            contents = []

            # Add image if provided (for VLM import)
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                contents.append(img)

            contents.append(prompt)

            # Configure for structured output
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

            # Parse JSON into the schema
            raw_text = response.text
            if isinstance(raw_text, str):
                data = json.loads(raw_text)
            else:
                data = raw_text

            return schema.model_validate(data)

        except json.JSONDecodeError as e:
            raise GemmaClientError(f"Failed to parse Gemma output as JSON: {e}")
        except Exception as e:
            raise GemmaClientError(f"Gemma API call failed: {e}")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """
        Generate plain text output (for analysis, explanations, chat).

        Args:
            prompt: The user prompt.
            system_prompt: Optional system instruction.
            temperature: Higher for more creative output.

        Returns:
            Raw text string from the model.
        """
        try:
            contents = []
            if system_prompt:
                contents.append(f"System: {system_prompt}\n\n")
            contents.append(prompt)

            config = types.GenerateContentConfig(
                temperature=temperature,
            )

            response = self._client.models.generate_content(
                model=self._model,
                contents="".join(contents),
                config=config,
            )

            return response.text or ""

        except Exception as e:
            raise GemmaClientError(f"Gemma text generation failed: {e}")

    def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
    ) -> str:
        """
        Transcribe audio file using Gemma 4's audio understanding.

        Args:
            audio_path: Path to audio file (WAV, MP3, WebM).
            prompt: Optional instruction for transcription context.

        Returns:
            Transcribed text.
        """
        try:
            # Upload audio file
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
            raise GemmaClientError(f"Audio transcription failed: {e}")

    def health_check(self) -> dict:
        """
        Verify Gemma 4 connection is working.

        Returns:
            Dict with model name and status.
        """
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents="Say 'OK' if you can read this.",
            )
            return {
                "model": self._model,
                "status": "ok" if response.text else "error",
                "response_preview": (response.text or "")[:50],
            }
        except Exception as e:
            return {
                "model": self._model,
                "status": "error",
                "error": str(e),
            }


# Singleton instance (lazy-initialized)
_gemma_client: Optional[GemmaClient] = None


def get_gemma_client() -> GemmaClient:
    """Get or create the singleton GemmaClient instance."""
    global _gemma_client
    if _gemma_client is None:
        _gemma_client = GemmaClient()
    return _gemma_client
