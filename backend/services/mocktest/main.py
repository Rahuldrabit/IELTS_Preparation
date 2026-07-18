"""Mock Test Service - Full IELTS simulation with timed sections."""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_db
from shared.models import MockTest, MockTestSection, User
from services.mocktest.baseline_data import (
    get_baseline_section_content,
    SECTION_TIMING,
    SECTION_ORDER,
)
from services.mocktest.generator import (
    generate_listening_content,
    generate_reading_content,
    generate_writing_content,
    generate_speaking_content,
)
from services.mocktest.imported_tests import (
    get_imported_test,
    get_imported_test_list,
    IMPORTED_TESTS,
)


# ============ Router ============

router = APIRouter(prefix="/mocktest", tags=["MockTest"])


# ============ Pydantic Schemas ============

class MockTestSectionResponse(BaseModel):
    id: int
    section_type: str
    section_order: int
    status: str
    time_allocated_seconds: int
    time_spent_seconds: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    band_estimate: Optional[float] = None
    difficulty_config: Optional[list | dict] = None

    class Config:
        from_attributes = True


class MockTestResponse(BaseModel):
    id: int
    test_type: str
    status: str
    overall_band: Optional[float] = None
    listening_band: Optional[float] = None
    reading_band: Optional[float] = None
    writing_band: Optional[float] = None
    speaking_band: Optional[float] = None
    started_at: str
    finished_at: Optional[str] = None
    total_time_seconds: Optional[int] = None
    sections: List[MockTestSectionResponse] = []

    class Config:
        from_attributes = True


class MockTestHistoryItem(BaseModel):
    id: int
    test_type: str
    status: str
    overall_band: Optional[float] = None
    listening_band: Optional[float] = None
    reading_band: Optional[float] = None
    writing_band: Optional[float] = None
    speaking_band: Optional[float] = None
    started_at: str
    finished_at: Optional[str] = None
    total_time_seconds: Optional[int] = None


class MockTestDetailResponse(BaseModel):
    """Full mock test with section content for active test."""
    id: int
    test_type: str
    status: str
    overall_band: Optional[float] = None
    listening_band: Optional[float] = None
    reading_band: Optional[float] = None
    writing_band: Optional[float] = None
    speaking_band: Optional[float] = None
    started_at: str
    finished_at: Optional[str] = None
    total_time_seconds: Optional[int] = None
    sections: List[dict] = []
    diagnostic_report: Optional[dict] = None


class SectionSubmitRequest(BaseModel):
    """Submit answers for a section."""
    answers: dict = Field(description="User answers for this section")
    time_spent_seconds: int = Field(description="Time spent on this section in seconds")


class StartMockTestRequest(BaseModel):
    """Optional configuration for starting a mock test."""
    test_type: Optional[str] = Field(
        default=None,
        description="Force 'baseline' or 'generated'. Auto-detects if None."
    )


# ============ Helper Functions ============

def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string."""
    return dt.isoformat() if dt else None


def _build_section_response(section: MockTestSection) -> MockTestSectionResponse:
    """Convert a MockTestSection model to response schema."""
    return MockTestSectionResponse(
        id=section.id,
        section_type=section.section_type,
        section_order=section.section_order,
        status=section.status,
        time_allocated_seconds=section.time_allocated_seconds,
        time_spent_seconds=section.time_spent_seconds,
        started_at=_serialize_datetime(section.started_at),
        finished_at=_serialize_datetime(section.finished_at),
        band_estimate=float(section.band_estimate) if section.band_estimate else None,
        difficulty_config=section.difficulty_config,
    )


def _build_mock_test_response(mock_test: MockTest) -> MockTestResponse:
    """Convert a MockTest model to response schema."""
    return MockTestResponse(
        id=mock_test.id,
        test_type=mock_test.test_type,
        status=mock_test.status,
        overall_band=float(mock_test.overall_band) if mock_test.overall_band else None,
        listening_band=float(mock_test.listening_band) if mock_test.listening_band else None,
        reading_band=float(mock_test.reading_band) if mock_test.reading_band else None,
        writing_band=float(mock_test.writing_band) if mock_test.writing_band else None,
        speaking_band=float(mock_test.speaking_band) if mock_test.speaking_band else None,
        started_at=mock_test.started_at.isoformat(),
        finished_at=_serialize_datetime(mock_test.finished_at),
        total_time_seconds=mock_test.total_time_seconds,
        sections=[_build_section_response(s) for s in mock_test.sections],
    )


# ============ Endpoints ============

@router.get("/imported-tests")
async def list_imported_tests():
    """Get list of available pre-built imported mock tests."""
    return get_imported_test_list()


@router.post("/start-imported/{test_id}")
async def start_imported_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Start a specific imported mock test by its ID."""
    imported = get_imported_test(test_id)
    if not imported:
        raise HTTPException(status_code=404, detail=f"Imported test '{test_id}' not found")

    # Abandon any existing in-progress test
    result = await db.execute(
        select(MockTest).where(
            and_(MockTest.user_id == 1, MockTest.status == "in_progress")
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.status = "abandoned"
        existing.finished_at = datetime.utcnow()

    now = datetime.utcnow()
    mock_test = MockTest(
        user_id=1,
        test_type="imported",
        status="in_progress",
        started_at=now,
        created_at=now,
        section_data=imported,
    )
    db.add(mock_test)
    await db.flush()

    # Create sections based on what's available in the imported test
    for section_type, order in SECTION_ORDER.items():
        section_content = imported.get(section_type)
        if section_content is None:
            # Skip sections that don't exist in this imported test
            continue

        section = MockTestSection(
            mock_test_id=mock_test.id,
            section_type=section_type,
            section_order=order,
            status="pending",
            time_allocated_seconds=SECTION_TIMING[section_type],
            content_data=section_content,
            difficulty_config=section_content.get("difficulty_config"),
        )
        db.add(section)

    await db.commit()
    await db.refresh(mock_test, attribute_names=["sections"])
    return _build_mock_test_response(mock_test)


@router.get("/baseline-status")
async def get_baseline_status(db: AsyncSession = Depends(get_db)):
    """Check if the user has completed the baseline mock test."""
    result = await db.execute(
        select(MockTest).where(
            and_(
                MockTest.user_id == 1,
                MockTest.test_type == "baseline",
                MockTest.status == "completed",
            )
        )
    )
    baseline = result.scalar_one_or_none()
    return {
        "has_completed_baseline": baseline is not None,
        "baseline_id": baseline.id if baseline else None,
        "baseline_band": float(baseline.overall_band) if baseline and baseline.overall_band else None,
    }


@router.post("/start")
async def start_mock_test(
    request: StartMockTestRequest = StartMockTestRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new mock test.
    - If user hasn't taken baseline yet (or request forces 'baseline'), loads pre-built test.
    - Otherwise, creates a 'generated' test (content generated on-the-fly per section).
    """
    # Determine test type
    if request.test_type:
        test_type = request.test_type
    else:
        # Auto-detect: check if baseline has been completed
        result = await db.execute(
            select(MockTest).where(
                and_(
                    MockTest.user_id == 1,
                    MockTest.test_type == "baseline",
                    MockTest.status == "completed",
                )
            )
        )
        has_baseline = result.scalar_one_or_none() is not None
        test_type = "generated" if has_baseline else "baseline"

    # Check for an existing in-progress test
    result = await db.execute(
        select(MockTest).where(
            and_(
                MockTest.user_id == 1,
                MockTest.status == "in_progress",
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # Abandon the existing in-progress test
        existing.status = "abandoned"
        existing.finished_at = datetime.utcnow()

    # Create the mock test
    now = datetime.utcnow()
    mock_test = MockTest(
        user_id=1,
        test_type=test_type,
        status="in_progress",
        started_at=now,
        created_at=now,
    )

    # Load content for baseline, or leave empty for generated (filled per-section)
    if test_type == "baseline":
        content = get_baseline_section_content()
        mock_test.section_data = content
    else:
        mock_test.section_data = None

    db.add(mock_test)
    await db.flush()

    # Create sections
    for section_type, order in SECTION_ORDER.items():
        difficulty_config = None
        content_data = None

        if test_type == "baseline":
            content = get_baseline_section_content()
            content_data = content.get(section_type)
            difficulty_config = content_data.get("difficulty_config") if content_data else None

        section = MockTestSection(
            mock_test_id=mock_test.id,
            section_type=section_type,
            section_order=order,
            status="pending",
            time_allocated_seconds=SECTION_TIMING[section_type],
            content_data=content_data,
            difficulty_config=difficulty_config,
        )
        db.add(section)

    await db.commit()
    await db.refresh(mock_test, attribute_names=["sections"])

    return _build_mock_test_response(mock_test)


@router.get("/history")
async def get_mock_test_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get list of past mock tests for the user."""
    result = await db.execute(
        select(MockTest)
        .where(MockTest.user_id == 1)
        .order_by(desc(MockTest.created_at))
        .offset(offset)
        .limit(limit)
    )
    tests = result.scalars().all()

    return [
        MockTestHistoryItem(
            id=t.id,
            test_type=t.test_type,
            status=t.status,
            overall_band=float(t.overall_band) if t.overall_band else None,
            listening_band=float(t.listening_band) if t.listening_band else None,
            reading_band=float(t.reading_band) if t.reading_band else None,
            writing_band=float(t.writing_band) if t.writing_band else None,
            speaking_band=float(t.speaking_band) if t.speaking_band else None,
            started_at=t.started_at.isoformat(),
            finished_at=_serialize_datetime(t.finished_at),
            total_time_seconds=t.total_time_seconds,
        )
        for t in tests
    ]


@router.get("/latest")
async def get_latest_mock_test(db: AsyncSession = Depends(get_db)):
    """Get the most recent mock test (in-progress or last completed)."""
    # First try in-progress
    result = await db.execute(
        select(MockTest)
        .where(and_(MockTest.user_id == 1, MockTest.status == "in_progress"))
        .order_by(desc(MockTest.created_at))
        .limit(1)
    )
    test = result.scalar_one_or_none()

    if not test:
        # Fall back to latest completed
        result = await db.execute(
            select(MockTest)
            .where(MockTest.user_id == 1)
            .order_by(desc(MockTest.created_at))
            .limit(1)
        )
        test = result.scalar_one_or_none()

    if not test:
        return None

    await db.refresh(test, attribute_names=["sections"])
    return _build_mock_test_response(test)


@router.get("/{mock_test_id}")
async def get_mock_test(mock_test_id: int, db: AsyncSession = Depends(get_db)):
    """Get full mock test details including section content (for resuming or reviewing)."""
    result = await db.execute(
        select(MockTest).where(
            and_(MockTest.id == mock_test_id, MockTest.user_id == 1)
        )
    )
    mock_test = result.scalar_one_or_none()

    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")

    await db.refresh(mock_test, attribute_names=["sections"])

    # Build detailed response with content
    sections_detail = []
    for section in mock_test.sections:
        section_dict = {
            "id": section.id,
            "section_type": section.section_type,
            "section_order": section.section_order,
            "status": section.status,
            "time_allocated_seconds": section.time_allocated_seconds,
            "time_spent_seconds": section.time_spent_seconds,
            "started_at": _serialize_datetime(section.started_at),
            "finished_at": _serialize_datetime(section.finished_at),
            "band_estimate": float(section.band_estimate) if section.band_estimate else None,
            "difficulty_config": section.difficulty_config,
            "content_data": section.content_data,
            "answers": section.answers,
            "section_feedback": section.section_feedback,
        }
        sections_detail.append(section_dict)

    return MockTestDetailResponse(
        id=mock_test.id,
        test_type=mock_test.test_type,
        status=mock_test.status,
        overall_band=float(mock_test.overall_band) if mock_test.overall_band else None,
        listening_band=float(mock_test.listening_band) if mock_test.listening_band else None,
        reading_band=float(mock_test.reading_band) if mock_test.reading_band else None,
        writing_band=float(mock_test.writing_band) if mock_test.writing_band else None,
        speaking_band=float(mock_test.speaking_band) if mock_test.speaking_band else None,
        started_at=mock_test.started_at.isoformat(),
        finished_at=_serialize_datetime(mock_test.finished_at),
        total_time_seconds=mock_test.total_time_seconds,
        sections=sections_detail,
        diagnostic_report=mock_test.diagnostic_report,
    )


@router.patch("/{mock_test_id}/section/{section_type}/start")
async def start_section(
    mock_test_id: int,
    section_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a section as started (records start time for timer)."""
    result = await db.execute(
        select(MockTest).where(
            and_(MockTest.id == mock_test_id, MockTest.user_id == 1)
        )
    )
    mock_test = result.scalar_one_or_none()
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")
    if mock_test.status != "in_progress":
        raise HTTPException(status_code=400, detail="Mock test is not in progress")

    # Find the section
    result = await db.execute(
        select(MockTestSection).where(
            and_(
                MockTestSection.mock_test_id == mock_test_id,
                MockTestSection.section_type == section_type,
            )
        )
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_type}' not found")

    if section.status == "completed":
        raise HTTPException(status_code=400, detail="Section already completed")

    # For generated tests, produce content on first start if not yet generated
    if not section.content_data:
        try:
            if section_type == "listening":
                section.content_data = await generate_listening_content()
            elif section_type == "reading":
                section.content_data = await generate_reading_content()
            elif section_type == "writing":
                section.content_data = await generate_writing_content()
            elif section_type == "speaking":
                section.content_data = await generate_speaking_content()
            section.difficulty_config = section.content_data.get("difficulty_config")
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to generate content for {section_type}: {str(e)}"
            )

    section.status = "in_progress"
    section.started_at = datetime.utcnow()
    await db.commit()

    return {
        "status": "in_progress",
        "section_type": section_type,
        "started_at": section.started_at.isoformat(),
        "time_allocated_seconds": section.time_allocated_seconds,
        "content_data": section.content_data,
    }


@router.patch("/{mock_test_id}/section/{section_type}/submit")
async def submit_section(
    mock_test_id: int,
    section_type: str,
    request: SectionSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit answers for a section and mark it complete."""
    result = await db.execute(
        select(MockTest).where(
            and_(MockTest.id == mock_test_id, MockTest.user_id == 1)
        )
    )
    mock_test = result.scalar_one_or_none()
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")
    if mock_test.status != "in_progress":
        raise HTTPException(status_code=400, detail="Mock test is not in progress")

    # Find the section
    result = await db.execute(
        select(MockTestSection).where(
            and_(
                MockTestSection.mock_test_id == mock_test_id,
                MockTestSection.section_type == section_type,
            )
        )
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_type}' not found")

    if section.status == "completed":
        raise HTTPException(status_code=400, detail="Section already submitted")

    # Save answers and mark complete
    section.answers = request.answers
    section.time_spent_seconds = request.time_spent_seconds
    section.status = "completed"
    section.finished_at = datetime.utcnow()

    # Score the section immediately for listening/reading (objective answers)
    if section_type in ("listening", "reading") and section.content_data:
        score_info = _score_objective_section(section_type, section.content_data, request.answers)
        section.score = score_info["score"]
        section.band_estimate = score_info["band_estimate"]

    await db.commit()

    # Check if all sections are complete
    await db.refresh(mock_test, attribute_names=["sections"])
    all_complete = all(s.status == "completed" for s in mock_test.sections)

    return {
        "status": "completed",
        "section_type": section_type,
        "score": float(section.score) if section.score else None,
        "band_estimate": float(section.band_estimate) if section.band_estimate else None,
        "all_sections_complete": all_complete,
        "time_spent_seconds": section.time_spent_seconds,
    }


@router.post("/{mock_test_id}/abandon")
async def abandon_mock_test(
    mock_test_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Mark a mock test as abandoned."""
    result = await db.execute(
        select(MockTest).where(
            and_(MockTest.id == mock_test_id, MockTest.user_id == 1)
        )
    )
    mock_test = result.scalar_one_or_none()
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")

    mock_test.status = "abandoned"
    mock_test.finished_at = datetime.utcnow()
    await db.commit()

    return {"status": "abandoned", "id": mock_test_id}


# ============ Scoring Helpers ============

def _score_objective_section(
    section_type: str,
    content_data: dict,
    user_answers: dict,
) -> dict:
    """
    Score listening/reading sections by comparing answers to correct answers.
    Returns score percentage and estimated IELTS band.
    """
    correct_count = 0
    total_questions = 0

    if section_type == "listening":
        sections = content_data.get("sections", [])
        for section in sections:
            for question in section.get("questions", []):
                total_questions += 1
                q_id = str(question["id"])
                user_answer = user_answers.get(q_id, "").strip().lower()
                correct = str(question["correct_answer"]).strip().lower()
                if user_answer == correct:
                    correct_count += 1

    elif section_type == "reading":
        passages = content_data.get("passages", [])
        for passage in passages:
            for question in passage.get("questions", []):
                total_questions += 1
                q_id = str(question["id"])
                user_answer = user_answers.get(q_id, "").strip().lower()
                correct = str(question["correct_answer"]).strip().lower()
                if user_answer == correct:
                    correct_count += 1

    if total_questions == 0:
        return {"score": 0, "band_estimate": 0}

    score_pct = (correct_count / total_questions) * 100
    band_estimate = _score_to_band(correct_count, total_questions)

    return {
        "score": round(score_pct, 1),
        "band_estimate": band_estimate,
        "correct": correct_count,
        "total": total_questions,
    }


def _score_to_band(correct: int, total: int) -> float:
    """
    Convert raw score to IELTS band estimate.
    Uses approximate IELTS band conversion (40 questions scale).
    """
    # Normalize to 40-question scale
    if total == 0:
        return 0.0
    normalized = (correct / total) * 40

    # IELTS approximate band conversion table (Academic)
    if normalized >= 39:
        return 9.0
    elif normalized >= 37:
        return 8.5
    elif normalized >= 35:
        return 8.0
    elif normalized >= 33:
        return 7.5
    elif normalized >= 30:
        return 7.0
    elif normalized >= 27:
        return 6.5
    elif normalized >= 23:
        return 6.0
    elif normalized >= 19:
        return 5.5
    elif normalized >= 15:
        return 5.0
    elif normalized >= 12:
        return 4.5
    elif normalized >= 9:
        return 4.0
    elif normalized >= 6:
        return 3.5
    else:
        return 3.0


# ============ Evaluate Endpoint ============

@router.post("/{mock_test_id}/evaluate")
async def evaluate_mock_test_endpoint(
    mock_test_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger full AI diagnostic evaluation after all sections are complete.
    Updates the mock test with band scores and diagnostic report.
    """
    from services.mocktest.evaluator import evaluate_mock_test

    result = await db.execute(
        select(MockTest).where(
            and_(MockTest.id == mock_test_id, MockTest.user_id == 1)
        )
    )
    mock_test = result.scalar_one_or_none()
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")

    await db.refresh(mock_test, attribute_names=["sections"])

    # Verify all sections are complete
    incomplete = [s.section_type for s in mock_test.sections if s.status != "completed"]
    if incomplete:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot evaluate: sections not complete: {', '.join(incomplete)}"
        )

    # Get user's target band
    user_result = await db.execute(select(User).where(User.id == 1))
    user = user_result.scalar_one_or_none()
    target_band = float(user.target_band) if user else 7.0

    # Run evaluation
    try:
        report = await evaluate_mock_test(
            sections=mock_test.sections,
            target_band=target_band,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Evaluation failed: {str(e)}")

    # Update mock test with results
    mock_test.overall_band = report["overall_band"]
    mock_test.listening_band = report["listening_band"]
    mock_test.reading_band = report["reading_band"]
    mock_test.writing_band = report["writing_band"]
    mock_test.speaking_band = report["speaking_band"]
    mock_test.diagnostic_report = report
    mock_test.status = "completed"
    mock_test.finished_at = datetime.utcnow()

    # Calculate total time
    total_time = sum(
        s.time_spent_seconds or 0 for s in mock_test.sections
    )
    mock_test.total_time_seconds = total_time

    await db.commit()

    return {
        "status": "completed",
        "mock_test_id": mock_test_id,
        "overall_band": report["overall_band"],
        "listening_band": report["listening_band"],
        "reading_band": report["reading_band"],
        "writing_band": report["writing_band"],
        "speaking_band": report["speaking_band"],
        "diagnostic_report": report,
    }
