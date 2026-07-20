import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import ReadingPassage, ReadingQuestion, Session as PracticeSession, UserResponse
from shared.schemas import ExamOutput, GeneratedPassageResponse
from shared.exam_questions import iter_generated_questions, build_question_groups_public
from shared.answer_utils import answers_match
from shared.parsing import parse_json_from_response
from services.agents.reading import ReadingAgent

from .schemas import GenerateReadingRequest
from . import repository


def build_generation_prompt(config: GenerateReadingRequest) -> str:
    # Deprecated: Logic moved to services.agents.reading
    pass


async def store_generated_exam(exam: ExamOutput, db: AsyncSession) -> ReadingPassage:
    content = "\n\n".join([p.text for p in exam.paragraphs])
    word_count = len(content.split())

    passage = ReadingPassage(
        title=exam.title,
        content=content,
        word_count=word_count,
        difficulty=exam.generation_params.difficulty if exam.generation_params else "medium",
        generation_params=exam.generation_params.model_dump() if exam.generation_params else None,
    )
    passage = await repository.create_reading_passage(db, passage)

    for group, question in iter_generated_questions(exam):
        db_question = ReadingQuestion(
            passage_id=passage.id,
            question_text=question.prompt_text,
            question_type=group.question_type,
            group_id=group.group_id,
            question_number=question.question_number,
            options=question.local_options,
            correct_answer=question.backend_evaluation.correct_answer,
            explanation=question.backend_evaluation.evidence_text,
            question_evaluation=question.backend_evaluation.model_dump(),
        )
        await repository.create_reading_question(db, db_question)

    await db.commit()
    await db.refresh(passage, attribute_names=["questions"])
    return passage


def to_public_response(passage: ReadingPassage, session_id: int, paragraphs: list) -> GeneratedPassageResponse:
    question_groups = build_question_groups_public(
        questions=passage.questions,
        get_group_id=lambda q: q.group_id or "group_1",
    )

    return GeneratedPassageResponse(
        passage_id=passage.id,
        session_id=session_id,
        title=passage.title,
        paragraphs=paragraphs,
        question_groups=question_groups,
        generation_params=passage.generation_params,
    )


async def evaluate_submissions(
    session: PracticeSession,
    questions: dict,
    answers: list,
    db: AsyncSession,
) -> tuple:
    correct_count = 0
    results = []
    total = len(questions)

    for answer in answers:
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

        results.append({
            "question_id": question.id,
            "user_answer": answer.answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "explanation": question.explanation if not is_correct else None,
        })

    return correct_count, results, total


def complete_session(session: PracticeSession, score: float) -> None:
    session.score = score
    session.band_estimate = round((score / 100) * 9, 1)
    session.finished_at = datetime.utcnow()


async def generate_error_analysis(passage_content: str, question: ReadingQuestion, user_answer: str) -> dict:
    agent = ReadingAgent()
    default_evidence = question.question_evaluation.get("evidence_text", "") if question.question_evaluation else ""
    result = await agent.generate_error_analysis(
        passage_content=passage_content,
        question_text=question.question_text,
        correct_answer=question.correct_answer,
        user_answer=user_answer,
        default_evidence=default_evidence
    )
    return result.model_dump()
