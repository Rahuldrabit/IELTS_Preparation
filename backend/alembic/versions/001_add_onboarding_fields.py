"""Add onboarding fields to users table.

Revision ID: 001_onboarding
Revises: None
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_onboarding"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add onboarding-related columns to users table."""
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("native_language", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("occupation", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("education_level", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("ielts_module", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("reason_for_ielts", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("focus_skills", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("study_hours_per_day", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove onboarding columns from users table."""
    op.drop_column("users", "study_hours_per_day")
    op.drop_column("users", "focus_skills")
    op.drop_column("users", "reason_for_ielts")
    op.drop_column("users", "ielts_module")
    op.drop_column("users", "education_level")
    op.drop_column("users", "occupation")
    op.drop_column("users", "native_language")
    op.drop_column("users", "date_of_birth")
    op.drop_column("users", "onboarding_completed")
