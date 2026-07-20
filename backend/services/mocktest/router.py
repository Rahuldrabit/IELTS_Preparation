import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared import get_db
from shared.models import MockTest, MockTestSection

from services.mocktest.baseline_data import get_baseline_section_content, SECTION_TIMING, SECTION_ORDER
from services.mocktest.generator import generate_listening_content, generate_reading_content, generate_writing_content, generate_speaking_content
from services.mocktest.imported_tests import get_imported_test, get_imported_test_list
from services.mocktest.question_utils import score_objective_section

from . import schemas
from . import repository
from . import service

router = APIRouter(prefix="/mocktest", tags=["MockTest"])

@router.get("/imported-tests")
async def list_imported_tests():
    return get_imported_test_list()

@router.post("/start-imported/{test_id}")
async def start_imported_test(
    test_id: str,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    imported = get_imported_test(test_id)
    if not imported:
        raise HTTPException(status_code=404, detail=f"Imported test '{test_id}' not found")

    existing = await repository.get_in_progress_mock_test(db, user_id)
    if existing:
        existing.status = "abandoned"
        existing.finished_at = datetime.utcnow()

    now = datetime.utcnow()
    mock_test = MockTest(
        user_id=user_id,
        test_type="imported",
        status="in_progress",
        started_at=now,
        created_at=now,
        section_data=imported,
    )
    mock_test = await repository.create_mock_test(db, mock_test)

    for section_type, order in SECTION_ORDER.items():
        section_content = imported.get(section_type)
        if section_content is None:
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
        await repository.create_mock_test_section(db, section)

    await db.commit()
    await db.refresh(mock_test, attribute_names=["sections"])
    return service.build_mock_test_response(mock_test)

@router.get("/baseline-status")
async def get_baseline_status(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    baseline = await repository.get_completed_baseline_test(db, user_id)
    return {
        "has_completed_baseline": baseline is not None,
        "baseline_id": baseline.id if baseline else None,
        "baseline_band": float(baseline.overall_band) if baseline and baseline.overall_band else None,
    }

@router.post("/start")
async def start_mock_test(
    request: schemas.StartMockTestRequest = schemas.StartMockTestRequest(),
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    if request.test_type:
        test_type = request.test_type
    else:
        has_baseline = await repository.get_completed_baseline_test(db, user_id) is not None
        test_type = "generated" if has_baseline else "baseline"

    existing = await repository.get_in_progress_mock_test(db, user_id)
    if existing:
        existing.status = "abandoned"
        existing.finished_at = datetime.utcnow()

    now = datetime.utcnow()
    mock_test = MockTest(
        user_id=user_id,
        test_type=test_type,
        status="in_progress",
        started_at=now,
        created_at=now,
    )

    baseline_content = None
    if test_type == "baseline":
        baseline_content = get_baseline_section_content()
        mock_test.section_data = baseline_content
    else:
        mock_test.section_data = None

    mock_test = await repository.create_mock_test(db, mock_test)

    for section_type, order in SECTION_ORDER.items():
        difficulty_config = None
        content_data = None

        if test_type == "baseline" and baseline_content:
            content_data = baseline_content.get(section_type)
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
        await repository.create_mock_test_section(db, section)

    await db.commit()
    await db.refresh(mock_test, attribute_names=["sections"])

    return service.build_mock_test_response(mock_test)

@router.get("/history")
async def get_mock_test_history(
    limit: int = 20,
    offset: int = 0,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    tests = await repository.get_mock_test_history(db, user_id, limit, offset)
    return [
        schemas.MockTestHistoryItem(
            id=t.id,
            test_type=t.test_type,
            status=t.status,
            overall_band=float(t.overall_band) if t.overall_band else None,
            listening_band=float(t.listening_band) if t.listening_band else None,
            reading_band=float(t.reading_band) if t.reading_band else None,
            writing_band=float(t.writing_band) if t.writing_band else None,
            speaking_band=float(t.speaking_band) if t.speaking_band else None,
            started_at=t.started_at.isoformat(),
            finished_at=service.serialize_datetime(t.finished_at),
            total_time_seconds=t.total_time_seconds,
        )
        for t in tests
    ]

@router.get("/latest")
async def get_latest_mock_test(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    test = await repository.get_in_progress_mock_test(db, user_id)
    if not test:
        test = await repository.get_latest_completed_mock_test(db, user_id)
    if not test:
        return None

    await db.refresh(test, attribute_names=["sections"])
    return service.build_mock_test_response(test)

@router.get("/{mock_test_id}")
async def get_mock_test(mock_test_id: int, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    mock_test = await repository.get_mock_test(db, mock_test_id, user_id)
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")

    await db.refresh(mock_test, attribute_names=["sections"])

    sections_detail = []
    for section in mock_test.sections:
        section_dict = {
            "id": section.id,
            "section_type": section.section_type,
            "section_order": section.section_order,
            "status": section.status,
            "time_allocated_seconds": section.time_allocated_seconds,
            "time_spent_seconds": section.time_spent_seconds,
            "started_at": service.serialize_datetime(section.started_at),
            "finished_at": service.serialize_datetime(section.finished_at),
            "band_estimate": float(section.band_estimate) if section.band_estimate else None,
            "difficulty_config": section.difficulty_config,
            "content_data": section.content_data,
            "answers": section.answers,
            "section_feedback": section.section_feedback,
        }
        sections_detail.append(section_dict)

    return schemas.MockTestDetailResponse(
        id=mock_test.id,
        test_type=mock_test.test_type,
        status=mock_test.status,
        overall_band=float(mock_test.overall_band) if mock_test.overall_band else None,
        listening_band=float(mock_test.listening_band) if mock_test.listening_band else None,
        reading_band=float(mock_test.reading_band) if mock_test.reading_band else None,
        writing_band=float(mock_test.writing_band) if mock_test.writing_band else None,
        speaking_band=float(mock_test.speaking_band) if mock_test.speaking_band else None,
        started_at=mock_test.started_at.isoformat(),
        finished_at=service.serialize_datetime(mock_test.finished_at),
        total_time_seconds=mock_test.total_time_seconds,
        sections=sections_detail,
        diagnostic_report=mock_test.diagnostic_report,
    )

@router.patch("/{mock_test_id}/section/{section_type}/start")
async def start_section(
    mock_test_id: int,
    section_type: str,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    mock_test = await repository.get_mock_test(db, mock_test_id, user_id)
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")
    if mock_test.status != "in_progress":
        raise HTTPException(status_code=400, detail="Mock test is not in progress")

    section = await repository.get_mock_test_section(db, mock_test_id, section_type)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_type}' not found")

    if section.status == "completed":
        raise HTTPException(status_code=400, detail="Section already completed")

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
    request: schemas.SectionSubmitRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    mock_test = await repository.get_mock_test(db, mock_test_id, user_id)
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")
    if mock_test.status != "in_progress":
        raise HTTPException(status_code=400, detail="Mock test is not in progress")

    section = await repository.get_mock_test_section(db, mock_test_id, section_type)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_type}' not found")

    if section.status == "completed":
        raise HTTPException(status_code=400, detail="Section already submitted")

    section.answers = request.answers
    section.time_spent_seconds = request.time_spent_seconds
    section.status = "completed"
    section.finished_at = datetime.utcnow()

    if section_type in ("listening", "reading") and section.content_data:
        score_info = score_objective_section(section_type, section.content_data, request.answers)
        section.score = score_info["score"]
        section.band_estimate = score_info["band_estimate"]

    await db.commit()
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
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    mock_test = await repository.get_mock_test(db, mock_test_id, user_id)
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")

    mock_test.status = "abandoned"
    mock_test.finished_at = datetime.utcnow()
    await db.commit()

    return {"status": "abandoned", "id": mock_test_id}

@router.post("/{mock_test_id}/evaluate")
async def evaluate_mock_test_endpoint(
    mock_test_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    from services.mocktest.evaluator import evaluate_mock_test

    mock_test = await repository.get_mock_test(db, mock_test_id, user_id)
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")

    await db.refresh(mock_test, attribute_names=["sections"])

    incomplete = [s.section_type for s in mock_test.sections if s.status != "completed"]
    if incomplete:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot evaluate: sections not complete: {', '.join(incomplete)}"
        )

    user = await repository.get_user(db, user_id)
    target_band = float(user.target_band) if user else 7.0

    try:
        report = await evaluate_mock_test(
            sections=mock_test.sections,
            target_band=target_band,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Evaluation failed: {str(e)}")

    mock_test.overall_band = report["overall_band"]
    mock_test.listening_band = report["listening_band"]
    mock_test.reading_band = report["reading_band"]
    mock_test.writing_band = report["writing_band"]
    mock_test.speaking_band = report["speaking_band"]
    mock_test.diagnostic_report = report
    mock_test.status = "completed"
    mock_test.finished_at = datetime.utcnow()

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
