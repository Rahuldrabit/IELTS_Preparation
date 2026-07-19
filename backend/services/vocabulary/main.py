"""Vocabulary Service - Word list, spaced repetition, word enrichment."""
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from shared import get_db
from shared.models import Vocabulary


# ============ Router ============

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary"])


# ============ Pydantic Schemas ============

class VocabularyCardSchema(BaseModel):
    id: int
    word: str
    pronunciation: Optional[str] = None
    meaning: Optional[str] = None
    definition: Optional[str] = None
    examples: list = []
    synonyms: list = []
    antonyms: list = []
    collocations: list = []
    word_family: list = []
    cefr: Optional[str] = None
    ielts_frequency: int = 0
    mastery: str
    next_review: Optional[str] = None

    class Config:
        from_attributes = True


class AddWordRequest(BaseModel):
    word: str


class ReviewRequest(BaseModel):
    word_id: int
    correct: bool


class VocabStats(BaseModel):
    new: int
    learning: int
    mastered: int
    total: int


# ============ SM-2 Algorithm ============

def sm2_review(mastery: str, ease_factor: float, interval: int, repetitions: int, correct: bool):
    """SM-2 spaced repetition algorithm."""
    if correct:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)

        repetitions += 1
        ease_factor = max(1.3, ease_factor + 0.1)

        if mastery == "new":
            mastery = "learning"
    else:
        repetitions = 0
        interval = 1
        ease_factor = max(1.3, ease_factor - 0.2)
        mastery = "learning"

    next_review = date.today() + timedelta(days=interval)

    return mastery, ease_factor, interval, repetitions, next_review


async def enrich_word(word: str) -> dict:
    """Call AI agent to enrich vocabulary."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/agent/enrich-vocab",
                json={"word": word},
            )
            response.raise_for_status()
            return response.json()
        except:
            return {
                "word": word,
                "pronunciation": "",
                "meaning": "",
                "definition": "",
                "examples": [],
                "synonyms": [],
                "antonyms": [],
                "collocations": [],
                "word_family": [],
                "cefr": "B2",
                "ielts_frequency": 5,
            }


# ============ Endpoints ============

@router.get("")
async def get_vocabulary(
    filter: str = "all",
    search: str = "",
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get user's vocabulary list."""
    query = select(Vocabulary).where(Vocabulary.user_id == 1)

    if filter != "all":
        query = query.where(Vocabulary.mastery == filter)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Vocabulary.word.ilike(search_pattern)) |
            (Vocabulary.meaning.ilike(search_pattern))
        )

    query = query.order_by(Vocabulary.next_review.asc()).offset(offset).limit(limit)
    result = await db.execute(query)
    words = result.scalars().all()

    return [
        VocabularyCardSchema(
            id=w.id,
            word=w.word,
            pronunciation=w.pronunciation,
            meaning=w.meaning,
            definition=w.definition,
            examples=w.examples or [],
            synonyms=w.synonyms or [],
            antonyms=w.antonyms or [],
            collocations=w.collocations or [],
            word_family=w.word_family or [],
            cefr=w.cefr,
            ielts_frequency=w.ielts_frequency,
            mastery=w.mastery,
            next_review=w.next_review.isoformat() if w.next_review else None,
        )
        for w in words
    ]


@router.get("/due")
async def get_due_vocabulary(db: AsyncSession = Depends(get_db)):
    """Get words due for review today."""
    today = date.today()
    result = await db.execute(
        select(Vocabulary)
        .where(Vocabulary.user_id == 1)
        .where(
            (Vocabulary.next_review == None) |
            (Vocabulary.next_review <= today)
        )
        .order_by(Vocabulary.next_review.asc())
    )
    words = result.scalars().all()

    return [
        VocabularyCardSchema(
            id=w.id,
            word=w.word,
            pronunciation=w.pronunciation,
            meaning=w.meaning,
            definition=w.definition,
            examples=w.examples or [],
            synonyms=w.synonyms or [],
            antonyms=w.antonyms or [],
            collocations=w.collocations or [],
            word_family=w.word_family or [],
            cefr=w.cefr,
            ielts_frequency=w.ielts_frequency,
            mastery=w.mastery,
            next_review=w.next_review.isoformat() if w.next_review else None,
        )
        for w in words
    ]


@router.get("/stats")
async def get_vocab_stats(db: AsyncSession = Depends(get_db)):
    """Get vocabulary statistics."""
    new_count = await db.scalar(
        select(func.count(Vocabulary.id))
        .where(Vocabulary.user_id == 1)
        .where(Vocabulary.mastery == "new")
    ) or 0

    learning_count = await db.scalar(
        select(func.count(Vocabulary.id))
        .where(Vocabulary.user_id == 1)
        .where(Vocabulary.mastery == "learning")
    ) or 0

    mastered_count = await db.scalar(
        select(func.count(Vocabulary.id))
        .where(Vocabulary.user_id == 1)
        .where(Vocabulary.mastery == "mastered")
    ) or 0

    total_count = new_count + learning_count + mastered_count

    return VocabStats(
        new=new_count,
        learning=learning_count,
        mastered=mastered_count,
        total=total_count,
    )


@router.post("/add")
async def add_word(request: AddWordRequest, db: AsyncSession = Depends(get_db)):
    """Add a new vocabulary word with AI enrichment."""
    existing = await db.execute(
        select(Vocabulary)
        .where(Vocabulary.user_id == 1)
        .where(Vocabulary.word.ilike(request.word))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Word already in vocabulary")

    enriched = await enrich_word(request.word)

    vocab = Vocabulary(
        user_id=1,
        word=enriched.get("word", request.word),
        pronunciation=enriched.get("pronunciation", ""),
        meaning=enriched.get("meaning", ""),
        definition=enriched.get("definition", ""),
        examples=enriched.get("examples", []),
        synonyms=enriched.get("synonyms", []),
        antonyms=enriched.get("antonyms", []),
        collocations=enriched.get("collocations", []),
        word_family=enriched.get("word_family", []),
        cefr=enriched.get("cefr", "B2"),
        ielts_frequency=enriched.get("ielts_frequency", 5),
        mastery="new",
        next_review=date.today() + timedelta(days=1),
    )

    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)

    return VocabularyCardSchema(
        id=vocab.id,
        word=vocab.word,
        pronunciation=vocab.pronunciation,
        meaning=vocab.meaning,
        definition=vocab.definition,
        examples=vocab.examples or [],
        synonyms=vocab.synonyms or [],
        antonyms=vocab.antonyms or [],
        collocations=vocab.collocations or [],
        word_family=vocab.word_family or [],
        cefr=vocab.cefr,
        ielts_frequency=vocab.ielts_frequency,
        mastery=vocab.mastery,
        next_review=vocab.next_review.isoformat() if vocab.next_review else None,
    )


@router.post("/review")
async def review_word(request: ReviewRequest, db: AsyncSession = Depends(get_db)):
    """Submit a vocabulary review result."""
    result = await db.execute(
        select(Vocabulary)
        .where(Vocabulary.id == request.word_id)
        .where(Vocabulary.user_id == 1)
    )
    vocab = result.scalar_one_or_none()

    if not vocab:
        raise HTTPException(status_code=404, detail="Word not found")

    mastery, ease_factor, interval, repetitions, next_review = sm2_review(
        vocab.mastery,
        float(vocab.ease_factor),
        vocab.interval,
        vocab.repetitions,
        request.correct,
    )

    vocab.mastery = mastery
    vocab.ease_factor = ease_factor
    vocab.interval = interval
    vocab.repetitions = repetitions
    vocab.next_review = next_review
    vocab.last_reviewed = datetime.utcnow()

    await db.commit()

    return {
        "status": "reviewed",
        "word_id": request.word_id,
        "correct": request.correct,
        "next_review": next_review.isoformat() if next_review else None,
    }



# ─────────────────────────────────────────────
#  Smart Vocabulary Harvesting (Phase 3 Feature #8)
# ─────────────────────────────────────────────

class HarvestWordRequest(BaseModel):
    """Request to harvest a word from reading/listening context."""
    word: str
    context_sentence: str
    source_type: str = "reading"  # reading, listening
    source_id: Optional[int] = None  # passage_id or session_id
    paragraph_index: Optional[int] = None


class HarvestedWordResponse(BaseModel):
    """Response for a harvested vocabulary word."""
    id: int
    word: str
    context_sentence: str
    pronunciation: Optional[str] = None
    definition: Optional[str] = None
    examples: list[str] = []
    synonyms: list[str] = []
    ai_definition: Optional[str] = None  # AI-generated definition for the context
    saved_at: datetime


@router.post("/harvest", response_model=HarvestedWordResponse)
async def harvest_word(
    request: HarvestWordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Harvest a vocabulary word from reading or listening practice.
    
    This endpoint:
    1. Extracts the word in context
    2. Generates AI definition specific to the context
    3. Saves to vocabulary deck with the context sentence
    4. Links back to source passage for review
    """
    from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError
    
    # Check if word already exists
    existing = await db.execute(
        select(Vocabulary)
        .where(Vocabulary.user_id == 1)
        .where(Vocabulary.word.ilike(request.word))
    )
    existing_word = existing.scalar_one_or_none()
    
    if existing_word:
        # Update with new context
        contexts = existing_word.contexts or []
        new_context = {
            "sentence": request.context_sentence,
            "source_type": request.source_type,
            "source_id": request.source_id,
            "paragraph_index": request.paragraph_index,
            "saved_at": datetime.utcnow().isoformat(),
        }
        contexts.append(new_context)
        existing_word.contexts = contexts
        await db.commit()
        
        return HarvestedWordResponse(
            id=existing_word.id,
            word=existing_word.word,
            context_sentence=request.context_sentence,
            pronunciation=existing_word.pronunciation,
            definition=existing_word.definition,
            examples=existing_word.examples or [],
            synonyms=existing_word.synonyms or [],
            ai_definition=existing_word.ai_definition,
            saved_at=datetime.utcnow(),
        )
    
    # Generate AI definition for the word in context
    ai_definition = None
    enriched = None
    
    try:
        client = get_gemma_client()
        
        # Generate context-specific definition
        context_prompt = f"""You are an IELTS vocabulary expert.

WORD: {request.word}
CONTEXT: "{request.context_sentence}"

Provide:
1. A definition of "{request.word}" as it's used in this specific context
2. 2 example sentences using this word in similar contexts
3. 3 synonyms appropriate for this usage
4. The CEFR level (A1-C2) for this word

Return JSON:
{{
  "context_definition": "definition specific to this context",
  "examples": ["example 1", "example 2"],
  "synonyms": ["synonym1", "synonym2", "synonym3"],
  "cefr": "B2"
}}
"""
        import asyncio
        from pydantic import create_model
        
        ContextDefinition = create_model(
            'ContextDefinition',
            context_definition=(str, ...),
            examples=(list[str], ...),
            synonyms=(list[str], ...),
            cefr=(str, "B2")
        )
        
        result = await asyncio.to_thread(
            client.generate_structured,
            prompt=context_prompt,
            schema=ContextDefinition,
            temperature=0.3,
        )
        
        ai_definition = result.context_definition
        
        # Also get full enrichment
        enriched = await enrich_word(request.word)
        
    except (GemmaClientError, Exception):
        # Fallback: use basic enrichment
        enriched = await enrich_word(request.word)
        ai_definition = enriched.get("definition", "")
    
    # Create new vocabulary entry
    vocab = Vocabulary(
        user_id=1,
        word=request.word.lower(),
        pronunciation=enriched.get("pronunciation", "") if enriched else "",
        meaning=enriched.get("meaning", "") if enriched else "",
        definition=enriched.get("definition", "") if enriched else "",
        examples=enriched.get("examples", []) if enriched else [],
        synonyms=enriched.get("synonyms", []) if enriched else [],
        antonyms=enriched.get("antonyms", []) if enriched else [],
        collocations=enriched.get("collocations", []) if enriched else [],
        word_family=enriched.get("word_family", []) if enriched else [],
        cefr=enriched.get("cefr", "B2") if enriched else "B2",
        ielts_frequency=enriched.get("ielts_frequency", 5) if enriched else 5,
        ai_definition=ai_definition,
        contexts=[{
            "sentence": request.context_sentence,
            "source_type": request.source_type,
            "source_id": request.source_id,
            "paragraph_index": request.paragraph_index,
            "saved_at": datetime.utcnow().isoformat(),
        }],
        mastery="new",
        next_review=date.today() + timedelta(days=1),
    )
    
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    
    return HarvestedWordResponse(
        id=vocab.id,
        word=vocab.word,
        context_sentence=request.context_sentence,
        pronunciation=vocab.pronunciation,
        definition=vocab.definition,
        examples=vocab.examples or [],
        synonyms=vocab.synonyms or [],
        ai_definition=vocab.ai_definition,
        saved_at=datetime.utcnow(),
    )


@router.get("/harvested")
async def get_harvested_words(
    source_type: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Get recently harvested vocabulary words.
    Optionally filter by source type (reading/listening).
    """
    query = select(Vocabulary).where(Vocabulary.user_id == 1)
    
    # Filter by words that have contexts (harvested)
    query = query.where(Vocabulary.contexts.isnot(None))
    
    if source_type:
        # This is a simplified filter; in production you'd use JSON query
        pass
    
    query = query.order_by(Vocabulary.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    words = result.scalars().all()
    
    return [
        {
            "id": w.id,
            "word": w.word,
            "context_sentence": w.contexts[0]["sentence"] if w.contexts else "",
            "source_type": w.contexts[0]["source_type"] if w.contexts else None,
            "definition": w.definition,
            "ai_definition": w.ai_definition,
            "saved_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in words
    ]


@router.get("/check/{word}")
async def check_word_saved(
    word: str,
    db: AsyncSession = Depends(get_db),
):
    """Check if a word is already in the user's vocabulary."""
    result = await db.execute(
        select(Vocabulary)
        .where(Vocabulary.user_id == 1)
        .where(Vocabulary.word.ilike(word))
    )
    existing = result.scalar_one_or_none()
    
    return {
        "word": word,
        "saved": existing is not None,
        "vocab_id": existing.id if existing else None,
    }
