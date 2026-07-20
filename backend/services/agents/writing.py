from typing import Optional
from pydantic import BaseModel, Field
from services.agents.base import BaseAgent
from services.agents.registry import registry
from services.agents.council import run_council


class ExtractedEssay(BaseModel):
    """Result of VLM text extraction."""
    text: str
    word_count: int
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    warnings: list[str] = []


@registry.register
class WritingAgent(BaseAgent):
    name = "WritingAgent"
    description = "Handles handwritten essay extraction and basic writing tasks."

    async def extract_text_from_image(self, image_path: str) -> ExtractedEssay:
        prompt = """You are an expert at reading handwritten English text from images.

TASK: Extract ALL text from this handwritten IELTS essay image.

INSTRUCTIONS:
1. Read every word carefully, including those that are crossed out or corrected
2. Preserve the original paragraph structure
3. If a word is illegible, write [ILLEGIBLE]
4. Maintain original spelling (don't correct errors)
5. Include any notes or markings on the page

Return the extracted text with paragraph breaks preserved.

Also provide:
- Your confidence in the extraction (0.0 to 1.0)
- Any warnings about difficult-to-read sections
"""
        return await self.run_structured(
            prompt=prompt,
            schema=ExtractedEssay,
            image_path=image_path,
            temperature=0.1
        )
