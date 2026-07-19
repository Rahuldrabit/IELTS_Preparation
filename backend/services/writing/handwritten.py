"""
Handwritten Essay Upload - VLM text extraction and scoring.

Task 7: Handwritten Essay Upload
- Accept image upload (photo of handwritten essay)
- Use Vision Language Model to extract text
- Run through AI rubric scoring pipeline
- Support multiple image formats
"""
import os
import tempfile
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import UploadFile, HTTPException

from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError


# ─────────────────────────────────────────────
#  Schemas
# ─────────────────────────────────────────────

class ExtractedEssay(BaseModel):
    """Result of VLM text extraction."""
    text: str
    word_count: int
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    warnings: list[str] = []  # e.g., "Some text may be illegible"


class HandwrittenEssayScore(BaseModel):
    """Complete scoring result for a handwritten essay."""
    extracted_text: str
    word_count: int
    extraction_confidence: float
    task_response: float
    coherence: float
    lexical: float
    grammar: float
    overall: float
    feedback: dict
    corrections: list[dict]
    warnings: list[str]


# ─────────────────────────────────────────────
#  VLM Text Extraction
# ─────────────────────────────────────────────

async def extract_text_from_image(
    image_path: str,
    task_type: str = "task_2",
) -> ExtractedEssay:
    """
    Extract text from a handwritten essay image using VLM.
    
    Uses Google Gemini Vision (or compatible VLM) to:
    1. Read handwritten text from the image
    2. Preserve formatting and structure
    3. Estimate extraction confidence
    """
    try:
        client = get_gemma_client()
        
        if client.mode != "google":
            raise GemmaClientError("Handwritten essay extraction requires Google AI mode with vision support")
        
        # Read image file
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Use VLM to extract text
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

Format your response as JSON:
{
  "text": "The extracted essay text...",
  "confidence": 0.85,
  "warnings": ["Some words in paragraph 2 were difficult to read"]
}
"""
        
        # Call VLM with image
        result = client.generate_with_image(
            prompt=prompt,
            image_path=image_path,
            schema=ExtractedEssay,
            temperature=0.1,  # Low temperature for accuracy
        )
        
        return ExtractedEssay(
            text=result.text,
            word_count=len(result.text.split()),
            confidence=result.confidence,
            warnings=result.warnings,
        )
        
    except GemmaClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"VLM extraction failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {str(e)}"
        )


async def score_handwritten_essay(
    image_path: str,
    task_type: str = "task_2",
    topic: Optional[str] = None,
) -> HandwrittenEssayScore:
    """
    Complete pipeline: extract text from image and score the essay.
    """
    # Step 1: Extract text from image
    extracted = await extract_text_from_image(image_path, task_type)
    
    # Step 2: Score the extracted text using existing writing scoring
    from services.ai_agent.main import score_writing, WritingScoreRequest
    
    score_result = await score_writing(WritingScoreRequest(
        essay=extracted.text,
        task_type=task_type,
    ))
    
    # Step 3: Combine results
    all_warnings = list(extracted.warnings)
    if extracted.confidence < 0.8:
        all_warnings.append("Low extraction confidence - please verify the text is correct")
    
    return HandwrittenEssayScore(
        extracted_text=extracted.text,
        word_count=extracted.word_count,
        extraction_confidence=extracted.confidence,
        task_response=score_result.task_response,
        coherence=score_result.coherence,
        lexical=score_result.lexical,
        grammar=score_result.grammar,
        overall=score_result.overall,
        feedback=score_result.feedback,
        corrections=score_result.corrections,
        warnings=all_warnings,
    )


# ─────────────────────────────────────────────
#  Helper Functions
# ─────────────────────────────────────────────

def validate_image_file(file: UploadFile) -> str:
    """
    Validate uploaded image file.
    Returns the file extension if valid.
    """
    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
    }
    
    content_type = file.content_type or "application/octet-stream"
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: {content_type}. Supported: JPEG, PNG, WebP, HEIC"
        )
    
    return allowed_types[content_type]


async def save_temp_image(file: UploadFile, extension: str) -> str:
    """Save uploaded image to a temporary file."""
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension,
        prefix="handwritten_essay_"
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        return tmp.name


def cleanup_temp_file(path: str) -> None:
    """Remove temporary file."""
    try:
        os.unlink(path)
    except Exception:
        pass
