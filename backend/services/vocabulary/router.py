from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from .schemas import (
    VocabularyCardSchema, AddWordRequest, ReviewRequest, VocabStats,
    HarvestWordRequest, HarvestedWordResponse
)
from .service import sm2_review
from . import repository
from services.agents.vocabulary import VocabularyAgent


# ============ Router ============

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary"])


# ============ Endpoints ============

@router.get("", response_model=list[VocabularyCardSchema])
async def get_vocabulary(
    filter: str = "all",
    search: str = "",
    limit: int = 50,
    offset: int = 0,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Get user's vocabulary list."""
    words = await repository.get_vocabulary(db, user_id, filter, search, limit, offset)
    
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


@router.get("/due", response_model=list[VocabularyCardSchema])
async def get_due_vocabulary(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Get words due for review today."""
    words = await repository.get_due_vocabulary(db, user_id)
    
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


@router.get("/stats", response_model=VocabStats)
async def get_vocab_stats(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Get vocabulary statistics."""
    stats = await repository.get_vocab_stats(db, user_id)
    return VocabStats(**stats)


@router.post("/add", response_model=VocabularyCardSchema)
async def add_word(request: AddWordRequest, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Add a new vocabulary word with AI enrichment."""
    existing_word = await repository.get_vocabulary_by_word(db, request.word, user_id)
    if existing_word:
        raise HTTPException(status_code=400, detail="Word already in vocabulary")

    agent = VocabularyAgent()
    enriched = await agent.enrich_word(request.word)

    from shared.models import Vocabulary
    vocab = Vocabulary(
        user_id=user_id,
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
async def review_word(request: ReviewRequest, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Submit a vocabulary review result."""
    vocab = await repository.get_vocabulary_by_id(db, request.word_id, user_id)

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


@router.post("/harvest", response_model=HarvestedWordResponse)
async def harvest_word(
    request: HarvestWordRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """
    Harvest a vocabulary word from reading or listening practice.
    """
    from services.agents.vocabulary import VocabularyAgent
    from shared.models import Vocabulary
    
    existing_word = await repository.get_vocabulary_by_word(db, request.word, user_id)
    
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
        agent = VocabularyAgent()
        result = await agent.generate_context_definition(request.word, request.context_sentence)
        
        ai_definition = result.context_definition
        
        # Also get full enrichment
        enriched = await enrich_word(request.word)
        
    except (GemmaClientError, Exception):
        # Fallback: use basic enrichment
        enriched = await enrich_word(request.word)
        ai_definition = enriched.get("definition", "")
    
    # Create new vocabulary entry
    vocab = Vocabulary(
        user_id=user_id,
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
async def get_harvested_endpoint(
    source_type: Optional[str] = None,
    limit: int = 20,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """
    Get recently harvested vocabulary words.
    Optionally filter by source type (reading/listening).
    """
    words = await repository.get_harvested_words(db, user_id, source_type, limit)
    
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
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Check if a word is already in the user's vocabulary."""
    existing = await repository.get_vocabulary_by_word(db, word, user_id)
    
    return {
        "word": word,
        "saved": existing is not None,
        "vocab_id": existing.id if existing else None,
    }
