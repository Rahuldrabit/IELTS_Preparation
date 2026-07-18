"""Reading Service - AI-generated passages, questions, sessions, and scoring."""
import asyncio
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import ReadingPassage, ReadingQuestion, Session as PracticeSession, UserResponse
from shared.schemas import (
    ExamOutput,
    GenerationParams,
    GeneratedPassageResponse,
    QuestionGroupPublic,
    QuestionItemPublic,
    SubmitRequest,
    SubmitAndAnalyzeResponse,
    QuestionExplanation,
)
from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError


# ============ Router ============

router = APIRouter(prefix="/reading", tags=["Reading"])


# ============ Request/Response Schemas ============

class QuestionTypeConfig(BaseModel):
    """Configuration for one question type to generate."""
    type: str = Field(description="TRUE_FALSE_NOT_GIVEN | MATCHING_HEADINGS | SUMMARY_COMPLETION | MULTIPLE_CHOICE | SENTENCE_COMPLETION")
    count: int = Field(default=5, ge=1, le=10)


class GenerateReadingRequest(BaseModel):
    """User's configuration for generating a reading test."""
    difficulty: str = Field(default="intermediate", description="beginner | intermediate | advanced | ielts_6 | ielts_7 | ielts_8 | ielts_9")
    vocabulary_level: str = Field(default="academic", description="basic | medium | academic | c1 | c2")
    grammar_complexity: str = Field(default="medium", description="simple | medium | complex | mixed")
    topic: str = Field(default="technology", description="environment | science | history | technology | health | education | business | random")
    passage_length_words: int = Field(default=600, ge=300, le=1500)
    question_types: List[QuestionTypeConfig] = Field(
        default_factory=lambda: [
            QuestionTypeConfig(type="TRUE_FALSE_NOT_GIVEN", count=5),
        ]
    )


class PassageListItem(BaseModel):
    id: int
    title: str
    difficulty: str
    word_count: int


class PassageDetail(BaseModel):
    id: int
    title: str
    content: str
    word_count: int
    difficulty: str
    questions: list


# ============ Helper: Build Prompt ============

def build_generation_prompt(config: GenerateReadingRequest) -> str:
    """Build the system prompt for Gemma 4 to generate an IELTS reading test."""

    question_types_desc = []
    for qt in config.question_types:
        question_types_desc.append(f"- {qt.type}: {qt.count} questions")

    prompt = f"""You are an expert IELTS examiner. Generate an authentic IELTS Academic Reading passage and questions.

TARGET SPECIFICATIONS:
- Topic: {config.topic}
- Difficulty: {config.difficulty}
- Vocabulary Level: {config.vocabulary_level}
- Grammar Complexity: {config.grammar_complexity}
- Passage Length: approximately {config.passage_length_words} words

QUESTION TYPES TO GENERATE:
{chr(10).join(question_types_desc)}

REQUIREMENTS:
1. Create a cohesive, academic-style passage on the given topic
2. The passage should have 5-7 paragraphs, each labeled with a paragraph_id (A, B, C, D, E, F, G)
3. Generate each question type exactly as specified
4. For each question, provide:
   - The question text (prompt_text)
   - Options if applicable (for MATCHING_HEADINGS, MULTIPLE_CHOICE)
   - The correct answer
   - The paragraph where the answer can be found (paragraph_anchor_id)
   - Evidence text from the passage (evidence_text)
   - Analysis of why students might choose the wrong answer (cognitive_distractor_analysis)

5. For TRUE_FALSE_NOT_GIVEN: Options should be ["True", "False", "Not Given"]
6. For MATCHING_HEADINGS: Provide a list of headings as options, one correct per question
7. For SUMMARY_COMPLETION: Provide a summary text with blanks, and the correct word for each blank

Return the output as a valid JSON matching the ExamOutput schema."""

    return prompt


# ============ Helper: Store Generated Exam ============

async def store_generated_exam(
    exam: ExamOutput,
    db: AsyncSession,
) -> ReadingPassage:
    """Store the generated passage and questions in the database."""

    # Combine paragraphs into full content
    content = "\n\n".join([p.text for p in exam.paragraphs])
    word_count = len(content.split())

    # Create passage
    passage = ReadingPassage(
        title=exam.title,
        content=content,
        word_count=word_count,
        difficulty=exam.generation_params.difficulty if exam.generation_params else "medium",
        generation_params=exam.generation_params.model_dump() if exam.generation_params else None,
    )
    db.add(passage)
    await db.flush()  # Get the ID

    # Create questions from question groups
    for group in exam.question_groups:
        for q in group.questions:
            question = ReadingQuestion(
                passage_id=passage.id,
                question_text=q.prompt_text,
                question_type=group.question_type,
                group_id=group.group_id,
                question_number=q.question_number,
                options=q.local_options,
                correct_answer=q.backend_evaluation.correct_answer,
                explanation=q.backend_evaluation.evidence_text,  # Store evidence as explanation
                question_evaluation=q.backend_evaluation.model_dump(),
            )
            db.add(question)

    await db.commit()
    await db.refresh(passage, attribute_names=["questions"])

    return passage


# ============ Helper: Convert to Public Response ============

def to_public_response(passage: ReadingPassage, session_id: int, paragraphs: list) -> GeneratedPassageResponse:
    """Convert DB passage to frontend-safe response (strip answers)."""

    # Group questions by group_id
    questions_by_group = {}
    for q in passage.questions:
        if q.group_id not in questions_by_group:
            questions_by_group[q.group_id] = []
        questions_by_group[q.group_id].append(q)

    question_groups = []
    for group_id, questions in questions_by_group.items():
        # Get question type from first question
        question_type = questions[0].question_type if questions else "UNKNOWN"

        # Build instructions based on type
        instructions_map = {
            "TRUE_FALSE_NOT_GIVEN": "Do the following statements agree with the information given in the passage? Write TRUE if the statement agrees with the information, FALSE if the statement contradicts the information, or NOT GIVEN if there is no information on this.",
            "MATCHING_HEADINGS": "The passage has paragraphs labeled A-G. Which paragraph contains the following information? Write the correct letter, A-G.",
            "SUMMARY_COMPLETION": "Complete the summary below. Choose ONE WORD ONLY from the passage for each answer.",
            "MULTIPLE_CHOICE": "Choose the correct answer, A, B, C or D.",
            "SENTENCE_COMPLETION": "Complete each sentence with the correct ending, A-G, below.",
        }

        question_groups.append(QuestionGroupPublic(
            group_id=group_id or "group_1",
            question_type=question_type,
            instructions=instructions_map.get(question_type, "Answer the following questions."),
            questions=[
                QuestionItemPublic(
                    id=q.id,
                    question_number=q.question_number or (idx + 1),
                    prompt_text=q.question_text,
                    local_options=q.options,
                    question_type=q.question_type,
                    # Includes trap metadata for adversarial questions; None for standard
                    question_evaluation=q.question_evaluation if hasattr(q, 'question_evaluation') else None,
                )
                for idx, q in enumerate(sorted(questions, key=lambda x: x.question_number or 0))
            ],
        ))

    return GeneratedPassageResponse(
        passage_id=passage.id,
        session_id=session_id,
        title=passage.title,
        paragraphs=paragraphs,
        question_groups=question_groups,
        generation_params=passage.generation_params,
    )


# ============ Endpoints ============

@router.post("/generate")
async def generate_reading(
    config: GenerateReadingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new IELTS reading passage and questions using Gemma 4.
    Returns the passage and questions WITHOUT correct answers.
    """
    try:
        client = get_gemma_client()
        prompt = build_generation_prompt(config)

        # Call AI with structured output (sync call — run in thread to avoid blocking event loop)
        exam: ExamOutput = await asyncio.to_thread(
            client.generate_structured,
            prompt=prompt,
            schema=ExamOutput,
            temperature=0.0,
        )

        # Inject generation params if not provided
        if not exam.generation_params:
            exam.generation_params = GenerationParams(
                difficulty=config.difficulty,
                vocabulary_level=config.vocabulary_level,
                grammar_complexity=config.grammar_complexity,
                topic=config.topic,
                passage_length_words=config.passage_length_words,
            )

        # Store in database
        passage = await store_generated_exam(exam, db)

        # Create a session
        session = PracticeSession(
            user_id=1,  # MVP: hardcoded user
            skill="reading",
            passage_id=passage.id,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Convert to public response (strip answers)
        response = to_public_response(passage, session.id, exam.paragraphs)

        return response

    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/passages")
async def get_passages(
    limit: int = 20,
    offset: int = 0,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get list of reading passages."""
    query = select(ReadingPassage).order_by(ReadingPassage.created_at.desc())

    if difficulty:
        query = query.where(ReadingPassage.difficulty == difficulty)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    passages = result.scalars().all()

    return [
        PassageListItem(
            id=p.id,
            title=p.title,
            difficulty=p.difficulty,
            word_count=p.word_count,
        )
        for p in passages
    ]


@router.get("/passages/{passage_id}")
async def get_passage(passage_id: int, db: AsyncSession = Depends(get_db)):
    """Get full passage with questions (excluding correct answers)."""
    result = await db.execute(
        select(ReadingPassage).where(ReadingPassage.id == passage_id)
    )
    passage = result.scalar_one_or_none()

    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")

    questions_result = await db.execute(
        select(ReadingQuestion).where(ReadingQuestion.passage_id == passage_id)
    )
    questions = questions_result.scalars().all()

    return PassageDetail(
        id=passage.id,
        title=passage.title,
        content=passage.content,
        word_count=passage.word_count,
        difficulty=passage.difficulty,
        questions=[
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
    )


@router.get("/sessions/{session_id}/passage")
async def get_session_passage(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get the passage and questions for a given session (used by VLM import redirect)."""
    session_result = await db.execute(
        select(PracticeSession).where(
            and_(PracticeSession.id == session_id, PracticeSession.skill == "reading")
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.passage_id:
        raise HTTPException(status_code=404, detail="Session has no associated passage")

    return await get_passage(session.passage_id, db)


@router.post("/sessions")
async def create_session(
    passage_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Create a new reading practice session."""
    result = await db.execute(
        select(ReadingPassage).where(ReadingPassage.id == passage_id)
    )
    passage = result.scalar_one_or_none()

    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")

    session = PracticeSession(
        user_id=1,
        skill="reading",
        passage_id=passage_id,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {"session_id": session.id, "passage_id": passage_id}


@router.post("/sessions/{session_id}/submit")
async def submit_answers(
    session_id: int,
    submission: SubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit answers for a reading session and get scored results."""
    result = await db.execute(
        select(PracticeSession).where(
            and_(PracticeSession.id == session_id, PracticeSession.skill == "reading")
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.finished_at:
        raise HTTPException(status_code=400, detail="Session already submitted")

    passage_result = await db.execute(
        select(ReadingPassage).where(ReadingPassage.id == session.passage_id)
    )
    passage = passage_result.scalar_one()

    questions_result = await db.execute(
        select(ReadingQuestion).where(ReadingQuestion.passage_id == passage.id)
    )
    questions = {q.id: q for q in questions_result.scalars().all()}

    correct_count = 0
    results = []
    total = len(questions)

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
            reading_question_id=question.id,
            user_answer=answer.answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
        )
        db.add(response)

        results.append({
            "question_id": question.id,
            "user_answer": answer.answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "explanation": question.explanation if not is_correct else None,
        })

    score = (correct_count / total * 100) if total > 0 else 0
    band_estimate = round((score / 100) * 9, 1)

    session.score = score
    session.band_estimate = band_estimate
    session.finished_at = datetime.utcnow()

    await db.commit()

    return {
        "session_id": session.id,
        "score": round(score, 1),
        "total": total,
        "band_estimate": band_estimate,
        "results": results,
    }


@router.post("/sessions/{session_id}/submit-and-analyze")
async def submit_and_analyze(
    session_id: int,
    submission: SubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit answers and get detailed AI-powered error analysis.
    Returns per-question explanations including why_wrong and correct_strategy.
    """
    # Fetch session
    result = await db.execute(
        select(PracticeSession).where(
            and_(PracticeSession.id == session_id, PracticeSession.skill == "reading")
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.finished_at:
        raise HTTPException(status_code=400, detail="Session already submitted")

    # Fetch passage and questions
    passage_result = await db.execute(
        select(ReadingPassage).where(ReadingPassage.id == session.passage_id)
    )
    passage = passage_result.scalar_one()

    questions_result = await db.execute(
        select(ReadingQuestion).where(ReadingQuestion.passage_id == passage.id)
    )
    questions_list = questions_result.scalars().all()
    questions = {q.id: q for q in questions_list}

    # Score and collect results
    correct_count = 0
    results = []
    total = len(questions)

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

        # Store response
        response = UserResponse(
            session_id=session.id,
            reading_question_id=question.id,
            user_answer=answer.answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
        )
        db.add(response)

        # Build result with analysis
        if is_correct:
            results.append(QuestionExplanation(
                question_id=question.id,
                question_number=question.question_number or 0,
                question_text=question.question_text,
                question_type=question.question_type,
                options=question.options,
                is_correct=True,
                user_answer=answer.answer,
                correct_answer=question.correct_answer,
                evidence_text=question.question_evaluation.get("evidence_text", "") if question.question_evaluation else "",
                evidence_paragraph_id=question.question_evaluation.get("paragraph_anchor_id", "") if question.question_evaluation else "",
                mistake_type="None",
                why_wrong="Correct answer!",
                correct_strategy="",
            ))
        else:
            # Generate AI analysis for wrong answer
            analysis = await generate_error_analysis(
                passage.content,
                question,
                answer.answer,
            )

            results.append(QuestionExplanation(
                question_id=question.id,
                question_number=question.question_number or 0,
                question_text=question.question_text,
                question_type=question.question_type,
                options=question.options,
                is_correct=False,
                user_answer=answer.answer,
                correct_answer=question.correct_answer,
                evidence_text=question.question_evaluation.get("evidence_text", "") if question.question_evaluation else analysis.get("evidence_text", ""),
                evidence_paragraph_id=question.question_evaluation.get("paragraph_anchor_id", "") if question.question_evaluation else "",
                mistake_type=analysis.get("mistake_type", "Inference"),
                why_wrong=analysis.get("why_wrong", ""),
                correct_strategy=analysis.get("correct_strategy", ""),
            ))

    # Update session
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


async def generate_error_analysis(
    passage_content: str,
    question: ReadingQuestion,
    user_answer: str,
) -> dict:
    """Use Gemma 4 to analyze why the user got this question wrong."""

    prompt = f"""Analyze this IELTS reading mistake and provide targeted feedback.

PASSAGE (excerpt):
{passage_content[:1000]}...

QUESTION:
{question.question_text}

CORRECT ANSWER: {question.correct_answer}
USER'S ANSWER: {user_answer}

Analyze the mistake and return JSON with these fields:
{{
    "mistake_type": "Inference | Vocabulary | Distractor | Skim-Scan | Detail",
    "why_wrong": "Explain in 1-2 sentences why the user chose this wrong answer",
    "correct_strategy": "Give a specific reading strategy to avoid this mistake next time",
    "evidence_text": "The exact sentence from the passage that proves the correct answer"
}}

Return ONLY valid JSON, no other text."""

    try:
        client = get_gemma_client()
        response = await asyncio.to_thread(client.generate_text, prompt, None, 0.3)

        # Try to parse JSON from response
        import json
        if "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            return json.loads(response[start:end])
    except Exception:
        pass

    # Fallback
    return {
        "mistake_type": "Inference",
        "why_wrong": f"You answered '{user_answer}' but the correct answer is '{question.correct_answer}'.",
        "correct_strategy": "Read the relevant paragraph more carefully and look for keywords that indicate the correct answer.",
        "evidence_text": question.question_evaluation.get("evidence_text", "") if question.question_evaluation else "",
    }


# ============ Socratic Debugging Agent ============
# All agent logic lives in services/agents/socratic/hint_engine.py
# This endpoint is a thin delegate — no LLM code here.

@router.post("/sessions/{session_id}/socratic-hint")
async def get_socratic_hint(
    session_id: int,
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Socratic Debugging Agent — delegates to SocraticHintAgent.
    Guides the student to the correct answer through structured questioning
    without ever revealing the answer directly.
    """
    from services.agents.socratic import SocraticHintAgent, SocraticHintRequest, ConversationTurn
    from services.ai_agent.gemma_client import GemmaClientError

    # Validate session exists
    result = await db.execute(
        select(PracticeSession).where(
            and_(PracticeSession.id == session_id, PracticeSession.skill == "reading")
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build the typed request
    history = [
        ConversationTurn(role=t["role"], text=t["text"])
        for t in request.get("conversation_history", [])
        if t.get("role") in ("agent", "student") and t.get("text")
    ]

    typed_request = SocraticHintRequest(
        question_text=request.get("question_text", ""),
        correct_answer=request.get("correct_answer", ""),
        user_answer=request.get("user_answer", ""),
        passage_excerpt=request.get("passage_excerpt", ""),
        question_type=request.get("question_type", "TRUE_FALSE_NOT_GIVEN"),
        conversation_history=history,
    )

    agent = SocraticHintAgent()
    try:
        return await agent.get_hint(typed_request)
    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Socratic hint failed: {str(e)}")


# ============ Adversarial Distractor Agent ============
# Delegates to AdversarialDistractorAgent. No LLM logic here.

@router.post("/adversarial/generate")
async def generate_adversarial(
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an adversarial reading set targeted at the student's
    personal cognitive blind spots (negative qualifiers, synonym traps, etc.).

    Accepts a StudentWeaknessProfile and returns an AdversarialQuestionSet
    ready to be loaded into the reading workspace.
    """
    from services.agents.adversarial import (
        AdversarialDistractorAgent,
        AdversarialGenerationRequest,
        StudentWeaknessProfile,
    )
    from services.ai_agent.gemma_client import GemmaClientError

    profile_data = request.get("weakness_profile", {})
    weakness_profile = StudentWeaknessProfile(
        wrong_question_types=profile_data.get("wrong_question_types", []),
        distractor_patterns_fallen_for=profile_data.get("distractor_patterns_fallen_for", []),
        low_confidence_win_topics=profile_data.get("low_confidence_win_topics", []),
        avg_time_per_question_ms=float(profile_data.get("avg_time_per_question_ms", 0)),
        target_band=float(profile_data.get("target_band", 7.0)),
    )

    gen_request = AdversarialGenerationRequest(
        weakness_profile=weakness_profile,
        topic=request.get("topic"),
        question_type=request.get("question_type", "TRUE_FALSE_NOT_GIVEN"),
        num_questions=min(int(request.get("num_questions", 4)), 5),
    )

    agent = AdversarialDistractorAgent()
    try:
        result = await agent.generate(gen_request)

        # Persist the generated passage and questions as a normal session
        # so the student can use the existing workspace UI
        passage = ReadingPassage(
            title=f"Adversarial Practice — {gen_request.question_type.replace('_', ' ').title()}",
            content=result.passage,
            word_count=len(result.passage.split()),
            difficulty="adversarial",
        )
        db.add(passage)
        await db.flush()

        for idx, q in enumerate(result.questions):
            question = ReadingQuestion(
                passage_id=passage.id,
                question_text=q.question_text,
                question_type=gen_request.question_type,
                group_id="adversarial_group",
                question_number=idx + 1,
                options=q.answer_options,
                correct_answer=q.correct_answer,
                explanation=q.trap_explanation,
                question_evaluation={
                    "evidence_text": q.evidence_paragraph_hint,
                    "paragraph_anchor_id": "",
                    "trap_type": q.trap_type,
                    "trap_explanation": q.trap_explanation,
                    "cognitive_distractor_analysis": q.trap_explanation,
                },
            )
            db.add(question)

        session = PracticeSession(
            user_id=1,
            skill="reading",
            passage_id=passage.id,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        await db.refresh(passage)

        return {
            "session_id": session.id,
            "passage_id": passage.id,
            "trap_summary": result.trap_summary,
            "difficulty_label": result.difficulty_label,
            "question_count": len(result.questions),
        }

    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adversarial generation failed: {str(e)}")
