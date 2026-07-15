"""Listening Service — AI-generated scripts, questions, sessions, browser TTS, scoring."""
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

    for group in exam.question_groups:
        for q in group.questions:
            question = ListeningQuestion(
                section_id=section.id,
                question_text=q.prompt_text,
                question_type=group.question_type,
                group_id=group.group_id,
                question_number=q.question_number,
                options=q.local_options,
                correct_answer=q.backend_evaluation.correct_answer,
                explanation=q.backend_evaluation.evidence_text,
                question_evaluation=q.backend_evaluation.model_dump(),
            )
            db.add(question)

    await db.commit()
    await db.refresh(section)
    return section


def _to_public_response(
    section: ListeningSection,
    session_id: int,
) -> GeneratedListeningResponse:
    """Convert DB section to frontend-safe response (strip answers)."""
    questions_by_group: dict[str, list] = {}
    for q in section.questions:
        gid = q.group_id or "group_1"
        if gid not in questions_by_group:
            questions_by_group[gid] = []
        questions_by_group[gid].append(q)

    question_groups = []
    for group_id, questions in questions_by_group.items():
        qtype = questions[0].question_type if questions else "UNKNOWN"
        instructions_map = {
            "FILL_BLANK": "Complete the notes below. Write ONE WORD AND/OR A NUMBER for each answer.",
            "MULTIPLE_CHOICE": "Choose the correct answer, A, B, C or D.",
            "MATCHING_INFORMATION": "Match each statement with the correct speaker. Write A, B or C.",
        }
        question_groups.append(QuestionGroupPublic(
            group_id=group_id,
            question_type=qtype,
            instructions=instructions_map.get(qtype, "Answer the following questions."),
            questions=[
                QuestionItemPublic(
                    id=q.id,
                    question_number=q.question_number or (idx + 1),
                    prompt_text=q.question_text,
                    local_options=q.options,
                    question_type=q.question_type,
                )
                for idx, q in enumerate(sorted(questions, key=lambda x: x.question_number or 0))
            ],
        ))

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
        response = client.generate_text(prompt, temperature=0.3)
        if "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            return json.loads(response[start:end])
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

        exam: ExamOutput = client.generate_structured(
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

        is_correct = (
            str(answer.answer).strip().lower()
            == str(question.correct_answer).strip().lower()
        )
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
