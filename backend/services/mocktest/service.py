from datetime import datetime
from typing import Optional
from shared.models import MockTest, MockTestSection
from .schemas import MockTestSectionResponse, MockTestResponse

def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None

def build_section_response(section: MockTestSection) -> MockTestSectionResponse:
    return MockTestSectionResponse(
        id=section.id,
        section_type=section.section_type,
        section_order=section.section_order,
        status=section.status,
        time_allocated_seconds=section.time_allocated_seconds,
        time_spent_seconds=section.time_spent_seconds,
        started_at=serialize_datetime(section.started_at),
        finished_at=serialize_datetime(section.finished_at),
        band_estimate=float(section.band_estimate) if section.band_estimate else None,
        difficulty_config=section.difficulty_config,
    )

def build_mock_test_response(mock_test: MockTest) -> MockTestResponse:
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
        finished_at=serialize_datetime(mock_test.finished_at),
        total_time_seconds=mock_test.total_time_seconds,
        sections=[build_section_response(s) for s in mock_test.sections],
    )
