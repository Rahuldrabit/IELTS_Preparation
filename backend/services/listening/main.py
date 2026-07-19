"""Listening Service — AI-generated scripts, questions, sessions, browser TTS, scoring."""
import asyncio
import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import ListeningSection, ListeningQuestion, Session as PracticeSession, UserResponse
from shared.schemas import (
    ExamOutput,
    GenerationParams,
    GeneratedListeningResponse,
    QuestionGroupPublic,
    QuestionItemPublic,
    ListeningGenerationParams,
    TTSConfig,
    SubmitRequest,
    SubmitAndAnalyzeResponse,
    QuestionExplanation,
)
from shared.exam_questions import (
    iter_generated_questions,
    build_question_groups_public,
)
from shared.answer_utils import answers_match
from shared.parsing import parse_json_from_response
from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError


# ============ Router ============

router = APIRouter(prefix="/listening", tags=["Listening"])


# ============ Request Schemas ============


class GenerateListeningRequest(BaseModel):
    """User's configuration for generating a listening test."""
    section: int = Field(default=1, ge=1, le=4, description="IELTS listening section 1-4")
    accent: str = Field(default="british", description="british | australian | american")
    speed: str = Field(default="normal", description="normal | exam | fast")
    topic: str = Field(default="general", description="Topic for the listening script")
    weakness_focus: List[str] = Field(default_factory=list)
    question_types: List[str] = Field(
        default_factory=lambda: ["FILL_BLANK"],
        description="Question types to generate",
    )
    question_count: int = Field(default=8, ge=4, le=12)


# ============ Helpers ============


def _build_generation_prompt(config: GenerateListeningRequest) -> str:
    """Build the system prompt for Gemma 4 to generate an IELTS listening test."""
    question_types_desc = ", ".join(config.question_types)

    return f"""You are an expert IELTS examiner. Generate a realistic IELTS Listening Section {config.section} script and questions.

TARGET SPECIFICATIONS:
- Section: {config.section}
- Accent: {config.accent}
- Speaking speed: {config.speed}
- Topic: {config.topic}
- Weakness focus areas: {', '.join(config.weakness_focus) if config.weakness_focus else 'none'}

SECTION CONTEXT:
- Section 1: Everyday social context (e.g., booking a hotel, enrolling in a course)
- Section 2: Social/monologue context (e.g., tour guide, information about an event)
- Section 3: Educational/training context (e.g., tutorial discussion, group project)
- Section 4: Academic lecture context

REQUIREMENTS:
1. Create a realistic dialogue or monologue (~{300 + config.section * 100} words) with natural speech patterns
2. Include speaker labels (e.g., "WOMAN:", "MAN:", "LECTURER:")
3. The transcript should have natural hesitations and connectors
4. Generate {config.question_count} questions of types: {question_types_desc}
5. For each question provide:
   - The question text (prompt_text)
   - Options if applicable (for MULTIPLE_CHOICE, MATCHING)
   - The correct answer
   - Evidence text from the transcript
   - Analysis of why students might choose wrong answer

6. For FILL_BLANK: The answer should be a word or short phrase from the transcript
7. For MULTIPLE_CHOICE: Provide options A-D

The passage (for schema compatibility) should contain a single paragraph with the full script text.
Use paragraph_id "S1" for the script.

Return JSON matching the ExamOutput schema."""


def _get_tts_config(accent: str, speed: str) -> TTSConfig:
    """Convert accent/speed to browser SpeechSynthesis config."""
    lang_map = {
        "british": "en-GB",
        "australian": "en-AU",
        "american": "en-US",
    }
    rate_map = {
        "normal": 0.9,
        "exam": 1.0,
        "fast": 1.15,
    }
    return TTSConfig(
        lang=lang_map.get(accent, "en-GB"),
        rate=rate_map.get(speed, 0.9),
        pitch=1.0,
    )


async def _store_generated_listening(
    exam: ExamOutput,
    config: GenerateListeningRequest,
    db: AsyncSession,
) -> ListeningSection:
    """Store generated listening section and questions in DB."""
    # Full transcript from paragraphs
    transcript = "\n\n".join([p.text for p in exam.paragraphs])
    word_count = len(transcript.split())

    tts = _get_tts_config(config.accent, config.speed)

    section = ListeningSection(
        title=exam.title,
        transcript=transcript,
        duration=max(60, int(word_count / 2.5)),  # ~2.5 words/sec
        difficulty=f"section_{config.section}",
        generation_params={
            "section": config.section,
            "accent": config.accent,
            "speed": config.speed,
            "topic": config.topic,
            "weakness_focus": config.weakness_focus,
            "question_types": config.question_types,
            "question_count": config.question_count,
        },
        tts_config=tts.model_dump(),
    )
    db.add(section)
    await db.flush()

    # Create questions using shared utility
    for group, question in iter_generated_questions(exam):
        db_question = ListeningQuestion(
            section_id=section.id,
            question_text=question.prompt_text,
            question_type=group.question_type,
            group_id=group.group_id,
            question_number=question.question_number,
            options=question.local_options,
            correct_answer=question.backend_evaluation.correct_answer,
            explanation=question.backend_evaluation.evidence_text,
            question_evaluation=question.backend_evaluation.model_dump(),
        )
        db.add(db_question)

    await db.commit()
    await db.refresh(section)
    return section


def _to_public_response(
    section: ListeningSection,
    session_id: int,
) -> GeneratedListeningResponse:
    """Convert DB section to frontend-safe response (strip answers)."""
    
    # Use shared utility to build question groups
    question_groups = build_question_groups_public(
        questions=section.questions,
        instructions_map={
            "FILL_BLANK": "Complete the notes below. Write ONE WORD AND/OR A NUMBER for each answer.",
            "MULTIPLE_CHOICE": "Choose the correct answer, A, B, C or D.",
            "MATCHING_INFORMATION": "Match each statement with the correct speaker. Write A, B or C.",
        },
        get_prompt_text=lambda q: q.question_text,
    )

    return GeneratedListeningResponse(
        section_id=section.id,
        session_id=session_id,
        title=section.title,
        script=section.transcript or "",
        tts_config=TTSConfig(**(section.tts_config or {"lang": "en-GB", "rate": 0.9})),
        question_groups=question_groups,
        generation_params=section.generation_params,
    )


async def _analyze_wrong_answer(
    transcript: str,
    question: ListeningQuestion,
    user_answer: str,
) -> dict:
    """Use Gemma 4 to analyze a wrong listening answer."""
    prompt = f"""Analyze this IELTS listening mistake and provide targeted feedback.

TRANSCRIPT:
{transcript[:1500]}

QUESTION:
{question.question_text}

CORRECT ANSWER: {question.correct_answer}
USER'S ANSWER: {user_answer}

The correct answer appears in the transcript. Analyze the mistake and return JSON:
{{
    "mistake_type": "Spelling | Misheard | Similar_Sound | Wrong_Speaker | Timing",
    "why_wrong": "Explain in 1-2 sentences why the user chose this wrong answer",
    "correct_strategy": "Give a specific listening strategy to avoid this mistake",
    "evidence_text": "The exact section of the transcript where the answer appears"
}}

Return ONLY valid JSON, no other text."""

    try:
        client = get_gemma_client()
        response = await asyncio.to_thread(client.generate_text, prompt, None, 0.3)
        result = parse_json_from_response(response)
        if result:
            return result
    except Exception:
        pass

    return {
        "mistake_type": "Misheard",
        "why_wrong": f"You answered '{user_answer}' but the correct answer is '{question.correct_answer}'.",
        "correct_strategy": "Listen more carefully for the specific information requested.",
        "evidence_text": question.question_evaluation.get("evidence_text", "") if question.question_evaluation else "",
    }


# ============ Endpoints ============


@router.post("/generate")
async def generate_listening(
    config: GenerateListeningRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a new IELTS listening test using Gemma 4. Returns script + questions without answers."""
    try:
        client = get_gemma_client()
        prompt = _build_generation_prompt(config)

        exam: ExamOutput = await asyncio.to_thread(
            client.generate_structured,
            prompt=prompt,
            schema=ExamOutput,
            temperature=0.0,
        )

        # Inject generation params if missing
        if not exam.generation_params:
            exam.generation_params = GenerationParams(
                difficulty=f"section_{config.section}",
                vocabulary_level="medium",
                grammar_complexity="medium",
                topic=config.topic,
                passage_length_words=400 + config.section * 100,
            )

        section = await _store_generated_listening(exam, config, db)

        # Create session
        session = PracticeSession(
            user_id=1,
            skill="listening",
            listening_section_id=section.id,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return _to_public_response(section, session.id)

    except GemmaClientError as e:
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
    query = select(ListeningSection).order_by(ListeningSection.created_at.desc())
    if difficulty:
        query = query.where(ListeningSection.difficulty == difficulty)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    tests = result.scalars().all()

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
    result = await db.execute(
        select(ListeningSection).where(ListeningSection.id == test_id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    questions_result = await db.execute(
        select(ListeningQuestion).where(ListeningQuestion.section_id == test_id)
    )
    questions = questions_result.scalars().all()

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
    result = await db.execute(
        select(PracticeSession).where(
            and_(PracticeSession.id == session_id, PracticeSession.skill == "listening")
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.finished_at:
        raise HTTPException(status_code=400, detail="Session already submitted")

    section_result = await db.execute(
        select(ListeningSection).where(ListeningSection.id == session.listening_section_id)
    )
    section = section_result.scalar_one()

    questions_result = await db.execute(
        select(ListeningQuestion).where(ListeningQuestion.section_id == section.id)
    )
    questions_list = questions_result.scalars().all()
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
        db.add(response)

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
            analysis = await _analyze_wrong_answer(transcript, question, answer.answer)
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


# ============ Acoustic Destabilization — Impulse Response Endpoint ============


@router.get("/audio/impulse-response")
async def get_impulse_response():
    """
    Serve a synthetic room impulse response (IR) as a WAV file.
    Used by the browser Web Audio ConvolverNode for Level 2 exam-room simulation.
    Cached for 24h — the IR never changes between requests.
    """
    import struct
    import math
    import random

    sample_rate = 44100
    duration_sec = 2.0
    num_samples = int(sample_rate * duration_sec)

    # Generate exponential-decay pink-noise IR
    # amplitude * exp(-t * decay) * noise
    decay = 3.0
    random.seed(42)  # deterministic so caching is valid
    samples_16bit: list[int] = []
    for i in range(num_samples):
        t = i / sample_rate
        amplitude = math.exp(-t * decay)
        noise = random.uniform(-1.0, 1.0)
        sample_f = amplitude * noise * 0.8          # keep headroom
        # Clamp and convert to 16-bit signed integer
        clamped = max(-1.0, min(1.0, sample_f))
        samples_16bit.append(int(clamped * 32767))

    # Build WAV file bytes (44-byte header + PCM data)
    data_size = num_samples * 2   # 16-bit = 2 bytes per sample
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,           # file size - 8
        b'WAVE',
        b'fmt ',
        16,                       # PCM chunk size
        1,                        # PCM format
        1,                        # mono
        sample_rate,
        sample_rate * 2,          # byte rate
        2,                        # block align
        16,                       # bits per sample
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


# ─────────────────────────────────────────────
#  Dictation Mode Endpoints
# ─────────────────────────────────────────────

class DictationSegment(BaseModel):
    """A single dictation segment with target text."""
    id: int
    text: str                    # Target text for this segment
    word_count: int
    difficulty: str = "medium"   # easy | medium | hard
    order: int                   # Sequence order


class DictationContentResponse(BaseModel):
    """Response with dictation content segmented into sentences."""
    section_id: int
    session_id: int
    title: str
    total_segments: int
    segments: list[DictationSegment]
    tts_config: TTSConfig


class DictationScoreRequest(BaseModel):
    """Request for scoring a dictation attempt."""
    segment_id: int
    typed_text: str


class WordDiff(BaseModel):
    """Word-level diff result."""
    word: str
    status: str  # correct | missing | extra | substituted
    expected: Optional[str] = None
    user_input: Optional[str] = None
    is_phonetic_confusion: bool = False
    phonetic_pair: Optional[str] = None


class DictationScoreResponse(BaseModel):
    """Response with word-level scoring."""
    segment_id: int
    accuracy: float              # 0.0 - 1.0
    correct_words: int
    total_words: int
    word_diffs: list[WordDiff]
    phonetic_confusions: list[dict]


# Common phonetic confusions in English
PHONETIC_CONFUSIONS = {
    # Numbers
    "thirteen": "thirty", "thirty": "thirteen",
    "fourteen": "forty", "forty": "fourteen",
    "fifteen": "fifty", "fifty": "fifteen",
    "sixteen": "sixty", "sixty": "sixteen",
    # Similar sounds
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


@router.post("/dictation/generate")
async def generate_dictation(
    config: Optional[GenerateListeningRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate dictation content from a listening script.
    Segments the transcript into sentences for pause-and-type practice.
    """
    import re
    
    # Default config if not provided
    if config is None:
        config = GenerateListeningRequest(
            section=2,
            accent="british",
            speed="normal",
            topic="everyday life",
            question_count=0,  # No questions for dictation
        )
    
    try:
        # Generate or use existing listening content
        client = get_gemma_client()
        
        # For dictation, generate a simpler, clearer script
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
        
        # Parse response using shared utility
        data = parse_json_from_response(response)
        if not data:
            raise ValueError("Invalid response from AI")
        
        script = data.get("script", "")
        title = data.get("title", f"Dictation - {config.topic}")
        
        # Segment into sentences
        # Use regex to split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', script)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        # Create listening section for storage
        tts = _get_tts_config(config.accent, config.speed)
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
        db.add(section)
        await db.flush()
        
        # Create session
        session = PracticeSession(
            user_id=1,
            skill="listening",
            listening_section_id=section.id,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()
        await db.refresh(section)
        await db.refresh(session)
        
        # Create segments
        segments = []
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            # Estimate difficulty by word length and sentence complexity
            avg_word_len = sum(len(w) for w in words) / len(words) if words else 5
            if avg_word_len > 6 or len(words) > 20:
                difficulty = "hard"
            elif avg_word_len > 4 or len(words) > 10:
                difficulty = "medium"
            else:
                difficulty = "easy"
            
            segments.append(DictationSegment(
                id=i + 1,
                text=sentence,
                word_count=len(words),
                difficulty=difficulty,
                order=i,
            ))
        
        return DictationContentResponse(
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


@router.post("/dictation/score", response_model=DictationScoreResponse)
async def score_dictation(
    request: DictationScoreRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Score a dictation attempt with word-level diff and phonetic confusion detection.
    """
    # Get the segment's target text (from the request context)
    # Note: In a real implementation, you'd fetch the target text from DB
    # For now, we'll compute the diff and store misses
    
    typed_words = request.typed_text.strip().split()
    # Target text would come from the segment - for now we'll need it passed
    # This is a simplified version
    
    # Actually, we need the target text. Let me adjust the approach:
    # The frontend should pass the target text along with the typed text
    # For now, return a placeholder
    
    raise HTTPException(
        status_code=400, 
        detail="Please use /dictation/score-full with both target and typed text"
    )


class DictationScoreFullRequest(BaseModel):
    """Request for scoring with both target and typed text."""
    segment_id: int
    session_id: int
    target_text: str
    typed_text: str


@router.post("/dictation/score-full", response_model=DictationScoreResponse)
async def score_dictation_full(
    request: DictationScoreFullRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Full dictation scoring with word-level diff and phonetic confusion detection.
    Persists misses to UserResponse for Error DNA integration.
    """
    target_words = request.target_text.strip().split()
    typed_words = request.typed_text.strip().split()
    
    # Normalize words for comparison
    def normalize(w):
        return w.lower().strip('.,!?;:"\'-')
    
    target_normalized = [normalize(w) for w in target_words]
    typed_normalized = [normalize(w) for w in typed_words]
    
    # Compute word-level alignment using simple diff
    word_diffs = []
    phonetic_confusions = []
    
    # Simple alignment: compare position by position
    max_len = max(len(target_words), len(typed_words))
    correct_count = 0
    
    for i in range(max_len):
        target_word = target_words[i] if i < len(target_words) else None
        typed_word = typed_words[i] if i < len(typed_words) else None
        
        target_norm = target_normalized[i] if i < len(target_normalized) else None
        typed_norm = typed_normalized[i] if i < len(typed_normalized) else None
        
        if target_word is None:
            # Extra word typed
            word_diffs.append(WordDiff(
                word=typed_word,
                status="extra",
                user_input=typed_word,
                is_phonetic_confusion=False,
            ))
        elif typed_word is None:
            # Missing word
            word_diffs.append(WordDiff(
                word=target_word,
                status="missing",
                expected=target_word,
                is_phonetic_confusion=False,
            ))
        elif target_norm == typed_norm:
            # Correct
            word_diffs.append(WordDiff(
                word=target_word,
                status="correct",
                is_phonetic_confusion=False,
            ))
            correct_count += 1
        else:
            # Substitution - check for phonetic confusion
            is_phonetic = False
            phonetic_pair = None
            
            if target_norm in PHONETIC_CONFUSIONS:
                if PHONETIC_CONFUSIONS[target_norm] == typed_norm:
                    is_phonetic = True
                    phonetic_pair = f"{target_norm}/{typed_norm}"
            
            word_diffs.append(WordDiff(
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
    
    # Store the miss as a UserResponse for Error DNA integration
    if accuracy < 1.0:
        # Get or create a "dictation" session entry
        session_result = await db.execute(
            select(PracticeSession).where(PracticeSession.id == request.session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if session:
            # Create a synthetic response record for dictation miss
            response = UserResponse(
                session_id=session.id,
                user_answer=request.typed_text,
                correct_answer=request.target_text,
                is_correct=(accuracy >= 0.8),  # Consider mostly correct as correct
                error_type="dictation_mishearing" if phonetic_confusions else "dictation_spelling",
                error_details={
                    "segment_id": request.segment_id,
                    "accuracy": accuracy,
                    "phonetic_confusions": phonetic_confusions,
                    "word_diffs": [wd.model_dump() for wd in word_diffs],
                },
            )
            db.add(response)
            await db.commit()
    
    return DictationScoreResponse(
        segment_id=request.segment_id,
        accuracy=round(accuracy, 3),
        correct_words=correct_count,
        total_words=len(target_words),
        word_diffs=word_diffs,
        phonetic_confusions=phonetic_confusions,
    )


class MishearingPair(BaseModel):
    """A single mishearing pair with count."""
    expected: str
    typed: str
    count: int
    last_occurrence: datetime


class MishearingProfileResponse(BaseModel):
    """User's mishearing profile from dictation practice."""
    total_attempts: int
    total_phonetic_confusions: int
    top_confusions: list[MishearingPair]


@router.get("/dictation/profile", response_model=MishearingProfileResponse)
async def get_dictation_profile(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the user's mishearing profile from dictation practice.
    Aggregates all phonetic confusions for Error DNA.
    """
    from collections import defaultdict
    
    # Get all dictation-related user responses
    result = await db.execute(
        select(UserResponse, PracticeSession)
        .join(PracticeSession, UserResponse.session_id == PracticeSession.id)
        .where(and_(
            PracticeSession.user_id == user_id,
            UserResponse.error_type == "dictation_mishearing",
        ))
        .order_by(UserResponse.created_at.desc())
    )
    rows = result.all()
    
    # Aggregate phonetic confusions
    confusion_counts: dict[tuple[str, str], int] = defaultdict(int)
    confusion_last_seen: dict[tuple[str, str], datetime] = {}
    
    for response, session in rows:
        details = response.error_details or {}
        for confusion in details.get("phonetic_confusions", []):
            key = (confusion.get("expected", ""), confusion.get("typed", ""))
            confusion_counts[key] += 1
            confusion_last_seen[key] = response.created_at
    
    # Sort by count
    top_confusions = sorted(
        confusion_counts.items(),
        key=lambda x: -x[1]
    )[:10]
    
    return MishearingProfileResponse(
        total_attempts=len(rows),
        total_phonetic_confusions=sum(confusion_counts.values()),
        top_confusions=[
            MishearingPair(
                expected=expected,
                typed=typed,
                count=count,
                last_occurrence=confusion_last_seen.get((expected, typed), datetime.utcnow()),
            )
            for (expected, typed), count in top_confusions
        ],
    )
