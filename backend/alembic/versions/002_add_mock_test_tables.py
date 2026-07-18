"""Add mock_tests and mock_test_sections tables.

Revision ID: 002_mock_tests
Revises: 001_onboarding
Create Date: 2024-01-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001_onboarding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create mock_tests and mock_test_sections tables."""
    op.create_table(
        "mock_tests",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("overall_band", sa.Numeric(3, 1), nullable=True),
        sa.Column("listening_band", sa.Numeric(3, 1), nullable=True),
        sa.Column("reading_band", sa.Numeric(3, 1), nullable=True),
        sa.Column("writing_band", sa.Numeric(3, 1), nullable=True),
        sa.Column("speaking_band", sa.Numeric(3, 1), nullable=True),
        sa.Column("diagnostic_report", sa.JSON(), nullable=True),
        sa.Column("section_data", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("total_time_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_mock_tests_user", "mock_tests", ["user_id"])
    op.create_index("idx_mock_tests_status", "mock_tests", ["user_id", "status"])

    op.create_table(
        "mock_test_sections",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("mock_test_id", sa.Integer(), sa.ForeignKey("mock_tests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_type", sa.String(20), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("time_allocated_seconds", sa.Integer(), nullable=False),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("content_data", sa.JSON(), nullable=True),
        sa.Column("answers", sa.JSON(), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("band_estimate", sa.Numeric(3, 1), nullable=True),
        sa.Column("section_feedback", sa.JSON(), nullable=True),
        sa.Column("difficulty_config", sa.JSON(), nullable=True),
    )
    op.create_index("idx_mock_test_sections_test", "mock_test_sections", ["mock_test_id"])


def downgrade() -> None:
    """Drop mock test tables."""
    op.drop_index("idx_mock_test_sections_test", table_name="mock_test_sections")
    op.drop_table("mock_test_sections")
    op.drop_index("idx_mock_tests_status", table_name="mock_tests")
    op.drop_index("idx_mock_tests_user", table_name="mock_tests")
    op.drop_table("mock_tests")
