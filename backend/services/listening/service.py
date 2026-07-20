import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import ListeningSection, ListeningQuestion
from shared.schemas import (
    ExamOutput,
    GeneratedListeningResponse,
    TTSConfig,
)
from shared.exam_questions import (
    iter_generated_questions,
    build_question_groups_public,
)
from shared.parsing import parse_json_from_response
from services.agents.listening import ListeningAgent

from .schemas import GenerateListeningRequest
from . import repository


def build_generation_prompt(config: GenerateListeningRequest) -> str:
    # Deprecated: Logic moved to services.agents.listening
    pass


def get_tts_config(accent: str, speed: str) -> TTSConfig:
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


async def store_generated_listening(
    exam: ExamOutput,
    config: GenerateListeningRequest,
    db: AsyncSession,
) -> ListeningSection:
    """Store generated listening section and questions in DB."""
    transcript = "\n\n".join([p.text for p in exam.paragraphs])
    word_count = len(transcript.split())

    tts = get_tts_config(config.accent, config.speed)

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
    
    section = await repository.create_listening_section(db, section)

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
        await repository.create_listening_question(db, db_question)

    await db.commit()
    await db.refresh(section)
    return section


def to_public_response(
    section: ListeningSection,
    session_id: int,
) -> GeneratedListeningResponse:
    """Convert DB section to frontend-safe response (strip answers)."""
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


async def analyze_wrong_answer(
    transcript: str,
    question: ListeningQuestion,
    user_answer: str,
) -> dict:
    """Use ListeningAgent to analyze a wrong listening answer."""
    agent = ListeningAgent()
    default_evidence = question.question_evaluation.get("evidence_text", "") if question.question_evaluation else ""
    result = await agent.analyze_wrong_answer(
        transcript=transcript,
        question_text=question.question_text,
        correct_answer=question.correct_answer,
        user_answer=user_answer,
        default_evidence=default_evidence
    )
    return result.model_dump()
