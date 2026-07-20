import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import Session as PracticeSession, UserResponse
from shared.schemas import (
    ExamOutput,
    GenerationParams,
    SubmitRequest,
    SubmitAndAnalyzeResponse,
    QuestionExplanation,
)
from shared.answer_utils import answers_match
from services.agents.listening import ListeningAgent
from services.llm import LLMClientError
from shared.parsing import parse_json_from_response

from . import schemas
from . import repository
from . import service

# ============ Router ============

router = APIRouter(prefix="/listening", tags=["Listening"])


@router.post("/generate")
async def generate_listening(
    config: schemas.GenerateListeningRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Generate a new IELTS listening test using Gemma 4. Returns script + questions without answers."""
    try:
        agent = ListeningAgent()
        exam: ExamOutput = await agent.generate_listening_section(
            section=config.section,
            accent=config.accent,
            speed=config.speed,
            topic=config.topic,
            weakness_focus=config.weakness_focus,
            question_types=config.question_types,
            question_count=config.question_count
        )

        if not exam.generation_params:
            exam.generation_params = GenerationParams(
                difficulty=f"section_{config.section}",
                vocabulary_level="medium",
                grammar_complexity="medium",
                topic=config.topic,
                passage_length_words=400 + config.section * 100,
            )

        section = await service.store_generated_listening(exam, config, db)

        session = PracticeSession(
            user_id=user_id,
            skill="listening",
            listening_section_id=section.id,
            started_at=datetime.utcnow(),
        )
        session = await repository.create_practice_session(db, session)

        return service.to_public_response(section, session.id)

    except LLMClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/tests")
async def get_tests(
    limit: int = 20,
    offset: int = 0,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get list of listening tests."""
    tests = await repository.get_listening_tests(db, limit, offset, difficulty)
    return [
        {
            "id": t.id,
            "title": t.title,
            "duration": t.duration,
            "difficulty": t.difficulty,
        }
        for t in tests
    ]


@router.get("/tests/{test_id}")
async def get_test(test_id: int, db: AsyncSession = Depends(get_db)):
    """Get full listening test with questions (excluding correct answers)."""
    test = await repository.get_listening_section(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    questions = await repository.get_listening_questions_by_section(db, test_id)

    return {
        "id": test.id,
        "title": test.title,
        "duration": test.duration,
        "transcript": test.transcript,
        "difficulty": test.difficulty,
        "tts_config": test.tts_config,
        "questions": [
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "group_id": q.group_id,
                "question_number": q.question_number,
            }
            for q in questions
        ],
    }


@router.post("/sessions/{session_id}/submit-and-analyze")
async def submit_and_analyze(
    session_id: int,
    submission: SubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit answers and get AI-powered error analysis for listening."""
    session = await repository.get_practice_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.finished_at:
        raise HTTPException(status_code=400, detail="Session already submitted")

    section = await repository.get_listening_section(db, session.listening_section_id)
    questions_list = await repository.get_listening_questions_by_section(db, section.id)
    questions = {q.id: q for q in questions_list}

    correct_count = 0
    results = []
    total = len(questions)
    transcript = section.transcript or ""

    for answer in submission.answers:
        question = questions.get(answer.question_id)
        if not question:
            continue

        is_correct = answers_match(answer.answer, question.correct_answer)
        if is_correct:
            correct_count += 1

        response = UserResponse(
            session_id=session.id,
            listening_question_id=question.id,
            user_answer=answer.answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
        )
        await repository.create_user_response(db, response)

        if is_correct:
            results.append(QuestionExplanation(
                question_id=question.id,
                question_number=question.question_number or 0,
                is_correct=True,
                user_answer=answer.answer,
                correct_answer=question.correct_answer,
                evidence_text=question.question_evaluation.get("evidence_text", "") if question.question_evaluation else "",
                evidence_paragraph_id="S1",
                mistake_type="None",
                why_wrong="Correct answer!",
                correct_strategy="",
            ))
        else:
            analysis = await service.analyze_wrong_answer(transcript, question, answer.answer)
            results.append(QuestionExplanation(
                question_id=question.id,
                question_number=question.question_number or 0,
                is_correct=False,
                user_answer=answer.answer,
                correct_answer=question.correct_answer,
                evidence_text=analysis.get("evidence_text", ""),
                evidence_paragraph_id="S1",
                mistake_type=analysis.get("mistake_type", "Misheard"),
                why_wrong=analysis.get("why_wrong", ""),
                correct_strategy=analysis.get("correct_strategy", ""),
            ))

    score = (correct_count / total * 100) if total > 0 else 0
    band_estimate = round((score / 100) * 9, 1)

    session.score = score
    session.band_estimate = band_estimate
    session.finished_at = datetime.utcnow()
    await db.commit()

    return SubmitAndAnalyzeResponse(
        session_id=session.id,
        score=round(score, 1),
        total=total,
        correct=correct_count,
        band_estimate=band_estimate,
        results=results,
    )


@router.get("/audio/impulse-response")
async def get_impulse_response():
    """Serve a synthetic room impulse response (IR) as a WAV file."""
    import struct
    import math
    import random

    sample_rate = 44100
    duration_sec = 2.0
    num_samples = int(sample_rate * duration_sec)

    decay = 3.0
    random.seed(42)
    samples_16bit: list[int] = []
    for i in range(num_samples):
        t = i / sample_rate
        amplitude = math.exp(-t * decay)
        noise = random.uniform(-1.0, 1.0)
        sample_f = amplitude * noise * 0.8
        clamped = max(-1.0, min(1.0, sample_f))
        samples_16bit.append(int(clamped * 32767))

    data_size = num_samples * 2
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b'data',
        data_size,
    )
    pcm_data = struct.pack(f'<{num_samples}h', *samples_16bit)
    wav_bytes = header + pcm_data

    from fastapi.responses import Response
    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"Cache-Control": "max-age=86400"},
    )


@router.post("/dictation/generate")
async def generate_dictation(
    config: Optional[schemas.GenerateListeningRequest] = None,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    import re
    from shared.models import ListeningSection

    if config is None:
        config = schemas.GenerateListeningRequest(
            section=2,
            accent="british",
            speed="normal",
            topic="everyday life",
            question_count=0,
        )
    
    try:
        client = get_gemma_client()
        prompt = f"""Generate a clear IELTS-style listening script for dictation practice.

SECTION: {config.section} ({"everyday social" if config.section <= 2 else "educational/academic"} context)
TOPIC: {config.topic}
ACCENT: {config.accent}

REQUIREMENTS:
1. Create a monologue or dialogue of about 200-300 words
2. Use clear, natural English appropriate for IELTS
3. Include proper names and numbers for realistic dictation
4. Avoid overly complex sentence structures
5. Make it sound like a real IELTS listening extract

Return JSON:
{{
  "title": "A descriptive title",
  "script": "The full script text with natural sentence boundaries..."
}}

Return ONLY valid JSON."""

        response = await asyncio.to_thread(
            client.generate_text,
            prompt,
            system_prompt="You are an IELTS content creator. Return only valid JSON.",
            temperature=0.7,
        )
        
        data = parse_json_from_response(response)
        if not data:
            raise ValueError("Invalid response from AI")
        
        script = data.get("script", "")
        title = data.get("title", f"Dictation - {config.topic}")
        
        sentences = re.split(r'(?<=[.!?])\s+', script)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        tts = service.get_tts_config(config.accent, config.speed)
        section = ListeningSection(
            title=title,
            transcript=script,
            duration=max(60, int(len(script.split()) / 2.5)),
            difficulty="dictation",
            generation_params={
                "mode": "dictation",
                "section": config.section,
                "accent": config.accent,
                "speed": config.speed,
                "topic": config.topic,
            },
            tts_config=tts.model_dump(),
        )
        section = await repository.create_listening_section(db, section)
        
        session = PracticeSession(
            user_id=user_id,
            skill="listening",
            listening_section_id=section.id,
            started_at=datetime.utcnow(),
        )
        session = await repository.create_practice_session(db, session)
        
        segments = []
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            avg_word_len = sum(len(w) for w in words) / len(words) if words else 5
            if avg_word_len > 6 or len(words) > 20:
                difficulty = "hard"
            elif avg_word_len > 4 or len(words) > 10:
                difficulty = "medium"
            else:
                difficulty = "easy"
            
            segments.append(schemas.DictationSegment(
                id=i + 1,
                text=sentence,
                word_count=len(words),
                difficulty=difficulty,
                order=i,
            ))
        
        return schemas.DictationContentResponse(
            section_id=section.id,
            session_id=session.id,
            title=title,
            total_segments=len(segments),
            segments=segments,
            tts_config=tts,
        )
        
    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dictation generation failed: {str(e)}")


PHONETIC_CONFUSIONS = {
    "thirteen": "thirty", "thirty": "thirteen",
    "fourteen": "forty", "forty": "fourteen",
    "fifteen": "fifty", "fifty": "fifteen",
    "sixteen": "sixty", "sixty": "sixteen",
    "their": "there", "there": "their",
    "affect": "effect", "effect": "affect",
    "accept": "except", "except": "accept",
    "advice": "advise", "advise": "advice",
    "practice": "practise", "practise": "practice",
    "principal": "principle", "principle": "principal",
    "stationary": "stationery", "stationery": "stationary",
    "complement": "compliment", "compliment": "complement",
    "bear": "bare", "bare": "bear",
    "brake": "break", "break": "brake",
    "buy": "bye", "bye": "buy",
    "cell": "sell", "sell": "cell",
    "flower": "flour", "flour": "flower",
    "hear": "here", "here": "hear",
    "hole": "whole", "whole": "hole",
    "know": "no", "no": "know",
    "mail": "male", "male": "mail",
    "meat": "meet", "meet": "meat",
    "peace": "piece", "piece": "peace",
    "plain": "plane", "plane": "plain",
    "right": "write", "write": "right",
    "sea": "see", "see": "sea",
    "son": "sun", "sun": "son",
    "steel": "steal", "steal": "steel",
    "tail": "tale", "tale": "tail",
    "weak": "week", "week": "weak",
    "wear": "where", "where": "wear",
    "wood": "would", "would": "wood",
}


@router.post("/dictation/score")
async def score_dictation(request: schemas.DictationScoreRequest):
    raise HTTPException(
        status_code=400, 
        detail="Please use /dictation/score-full with both target and typed text"
    )


@router.post("/dictation/score-full", response_model=schemas.DictationScoreResponse)
async def score_dictation_full(
    request: schemas.DictationScoreFullRequest,
    db: AsyncSession = Depends(get_db),
):
    target_words = request.target_text.strip().split()
    typed_words = request.typed_text.strip().split()
    
    def normalize(w):
        return w.lower().strip('.,!?;:"\'-')
    
    target_normalized = [normalize(w) for w in target_words]
    typed_normalized = [normalize(w) for w in typed_words]
    
    word_diffs = []
    phonetic_confusions = []
    
    max_len = max(len(target_words), len(typed_words))
    correct_count = 0
    
    for i in range(max_len):
        target_word = target_words[i] if i < len(target_words) else None
        typed_word = typed_words[i] if i < len(typed_words) else None
        
        target_norm = target_normalized[i] if i < len(target_normalized) else None
        typed_norm = typed_normalized[i] if i < len(typed_normalized) else None
        
        if target_word is None:
            word_diffs.append(schemas.WordDiff(
                word=typed_word,
                status="extra",
                user_input=typed_word,
                is_phonetic_confusion=False,
            ))
        elif typed_word is None:
            word_diffs.append(schemas.WordDiff(
                word=target_word,
                status="missing",
                expected=target_word,
                is_phonetic_confusion=False,
            ))
        elif target_norm == typed_norm:
            word_diffs.append(schemas.WordDiff(
                word=target_word,
                status="correct",
                is_phonetic_confusion=False,
            ))
            correct_count += 1
        else:
            is_phonetic = False
            phonetic_pair = None
            
            if target_norm in PHONETIC_CONFUSIONS:
                if PHONETIC_CONFUSIONS[target_norm] == typed_norm:
                    is_phonetic = True
                    phonetic_pair = f"{target_norm}/{typed_norm}"
            
            word_diffs.append(schemas.WordDiff(
                word=target_word,
                status="substituted",
                expected=target_word,
                user_input=typed_word,
                is_phonetic_confusion=is_phonetic,
                phonetic_pair=phonetic_pair,
            ))
            
            if is_phonetic:
                phonetic_confusions.append({
                    "expected": target_word,
                    "typed": typed_word,
                    "pair": phonetic_pair,
                })
    
    accuracy = correct_count / len(target_words) if target_words else 0.0
    
    if accuracy < 1.0:
        session = await repository.get_practice_session(db, request.session_id)
        if session:
            response = UserResponse(
                session_id=session.id,
                user_answer=request.typed_text,
                correct_answer=request.target_text,
                is_correct=(accuracy >= 0.8),
                error_type="dictation_mishearing" if phonetic_confusions else "dictation_spelling",
                error_details={
                    "segment_id": request.segment_id,
                    "accuracy": accuracy,
                    "phonetic_confusions": phonetic_confusions,
                    "word_diffs": [wd.model_dump() for wd in word_diffs],
                },
            )
            await repository.create_user_response(db, response)
            await db.commit()
    
    return schemas.DictationScoreResponse(
        segment_id=request.segment_id,
        accuracy=round(accuracy, 3),
        correct_words=correct_count,
        total_words=len(target_words),
        word_diffs=word_diffs,
        phonetic_confusions=phonetic_confusions,
    )


@router.get("/dictation/profile", response_model=schemas.MishearingProfileResponse)
async def get_dictation_profile(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    from collections import defaultdict
    
    rows = await repository.get_user_dictation_responses(db, user_id)
    
    confusion_counts: dict[tuple[str, str], int] = defaultdict(int)
    confusion_last_seen: dict[tuple[str, str], datetime] = {}
    
    for response, session in rows:
        details = response.error_details or {}
        for confusion in details.get("phonetic_confusions", []):
            key = (confusion.get("expected", ""), confusion.get("typed", ""))
            confusion_counts[key] += 1
            confusion_last_seen[key] = response.created_at
    
    top_confusions = sorted(
        confusion_counts.items(),
        key=lambda x: -x[1]
    )[:10]
    
    return schemas.MishearingProfileResponse(
        total_attempts=len(rows),
        total_phonetic_confusions=sum(confusion_counts.values()),
        top_confusions=[
            schemas.MishearingPair(
                expected=expected,
                typed=typed,
                count=count,
                last_occurrence=confusion_last_seen.get((expected, typed), datetime.utcnow()),
            )
            for (expected, typed), count in top_confusions
        ],
    )
