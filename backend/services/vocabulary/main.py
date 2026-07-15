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