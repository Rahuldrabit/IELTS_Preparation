from datetime import date, datetime, timedelta
import httpx


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
