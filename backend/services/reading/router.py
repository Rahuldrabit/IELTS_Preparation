import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared import get_db
from shared.models import Session as PracticeSession, UserResponse, ReadingPassage, ReadingQuestion
from shared.schemas import ExamOutput, GenerationParams, SubmitRequest, SubmitAndAnalyzeResponse, QuestionExplanation
from shared.answer_utils import answers_match
from services.agents.reading import ReadingAgent
from services.llm import LLMClientError

from . import schemas
from . import repository
from . import service

router = APIRouter(prefix="/reading", tags=["Reading"])

@router.post("/generate")
async def generate_reading(
    config: schemas.GenerateReadingRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    try:
        agent = ReadingAgent()
        exam: ExamOutput = await agent.generate_reading_passage(
            config_topic=config.topic,
            config_difficulty=config.difficulty,
            config_vocabulary_level=config.vocabulary_level,
            config_grammar_complexity=config.grammar_complexity,
            config_passage_length_words=config.passage_length_words,
            question_types=config.question_types
        )

        if not exam.generation_params:
            exam.generation_params = GenerationParams(
                difficulty=config.difficulty,
                vocabulary_level=config.vocabulary_level,
                grammar_complexity=config.grammar_complexity,
                topic=config.topic,
                passage_length_words=config.passage_length_words,
            )

        passage = await service.store_generated_exam(exam, db)

        session = PracticeSession(
            user_id=user_id,
            skill="reading",
            passage_id=passage.id,
            started_at=datetime.utcnow(),
        )
        session = await repository.create_practice_session(db, session)

        response = service.to_public_response(passage, session.id, exam.paragraphs)
        return response

    except LLMClientError as e:
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
    passages = await repository.get_reading_passages(db, limit, offset, difficulty)
    return [
        schemas.PassageListItem(
            id=p.id,
            title=p.title,
            difficulty=p.difficulty,
            word_count=p.word_count,
        )
        for p in passages
    ]


@router.get("/passages/{passage_id}")
async def get_passage(passage_id: int, db: AsyncSession = Depends(get_db)):
    passage = await repository.get_reading_passage(db, passage_id)
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")

    questions = await repository.get_reading_questions_by_passage(db, passage_id)

    return schemas.PassageDetail(
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
    session = await repository.get_practice_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.passage_id:
        raise HTTPException(status_code=404, detail="Session has no associated passage")

    return await get_passage(session.passage_id, db)


@router.post("/sessions")
async def create_session(
    passage_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    passage = await repository.get_reading_passage(db, passage_id)
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")

    session = PracticeSession(
        user_id=user_id,
        skill="reading",
        passage_id=passage_id,
        started_at=datetime.utcnow(),
    )
    session = await repository.create_practice_session(db, session)

    return {"session_id": session.id, "passage_id": passage_id}


async def _load_active_reading_session(session_id: int, db: AsyncSession):
    session = await repository.get_practice_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.finished_at:
        raise HTTPException(status_code=400, detail="Session already submitted")

    passage = await repository.get_reading_passage(db, session.passage_id)
    questions_list = await repository.get_reading_questions_by_passage(db, passage.id)
    questions = {q.id: q for q in questions_list}
    return session, passage, questions


@router.post("/sessions/{session_id}/submit")
async def submit_answers(
    session_id: int,
    submission: SubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    session, passage, questions = await _load_active_reading_session(session_id, db)
    correct_count, results, total = await service.evaluate_submissions(
        session, questions, submission.answers, db
    )
    score = (correct_count / total * 100) if total > 0 else 0
    service.complete_session(session, score)
    await db.commit()

    return {
        "session_id": session.id,
        "score": round(score, 1),
        "total": total,
        "band_estimate": round((score / 100) * 9, 1),
        "results": results,
    }


@router.post("/sessions/{session_id}/submit-and-analyze")
async def submit_and_analyze(
    session_id: int,
    submission: SubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    session, passage, questions = await _load_active_reading_session(session_id, db)

    correct_count = 0
    results = []
    total = len(questions)

    for answer in submission.answers:
        question = questions.get(answer.question_id)
        if not question:
            continue

        is_correct = answers_match(answer.answer, question.correct_answer)
        if is_correct:
            correct_count += 1

        response = UserResponse(
            session_id=session.id,
            reading_question_id=question.id,
            user_answer=answer.answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
        )
        await repository.create_user_response(db, response)

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
            analysis = await service.generate_error_analysis(
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

    score = (correct_count / total * 100) if total > 0 else 0
    service.complete_session(session, score)
    await db.commit()

    return SubmitAndAnalyzeResponse(
        session_id=session.id,
        score=round(score, 1),
        total=total,
        correct=correct_count,
        band_estimate=round((score / 100) * 9, 1),
        results=results,
    )


@router.post("/sessions/{session_id}/socratic-hint")
async def get_socratic_hint(
    session_id: int,
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    from services.agents.socratic import SocraticHintAgent, SocraticHintRequest, ConversationTurn

    session = await repository.get_practice_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

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


@router.post("/adversarial/generate")
async def generate_adversarial(
    request: dict,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    from services.agents.adversarial import (
        AdversarialDistractorAgent,
        AdversarialGenerationRequest,
        StudentWeaknessProfile,
    )

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

        passage = ReadingPassage(
            title=f"Adversarial Practice — {gen_request.question_type.replace('_', ' ').title()}",
            content=result.passage,
            word_count=len(result.passage.split()),
            difficulty="adversarial",
        )
        passage = await repository.create_reading_passage(db, passage)

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
            await repository.create_reading_question(db, question)

        session = PracticeSession(
            user_id=user_id,
            skill="reading",
            passage_id=passage.id,
            started_at=datetime.utcnow(),
        )
        session = await repository.create_practice_session(db, session)
        
        await db.commit()

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
