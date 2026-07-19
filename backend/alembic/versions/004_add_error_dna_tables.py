"""Add Error DNA tables

Revision ID: 004_add_error_dna_tables
Revises: grammar_module_tables
Create Date: 2024-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_error_dna_tables'
down_revision: Union[str, None] = 'grammar_module_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create error_signatures table
    op.create_table(
        'error_signatures',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill', sa.String(50), nullable=False),
        sa.Column('question_type', sa.String(100), nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('pattern_label', sa.String(200), nullable=False),
        sa.Column('pattern_key', sa.String(100), nullable=False),
        sa.Column('occurrences', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('severity', sa.String(20), nullable=True, server_default='medium'),
        sa.Column('example_refs', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create weekly_error_reports table
    op.create_table(
        'weekly_error_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('summary', sa.JSON(), nullable=False),
        sa.Column('signature_ids', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index('idx_error_signature_user_skill', 'error_signatures', ['user_id', 'skill'])
    op.create_index('idx_error_signature_user_pattern', 'error_signatures', ['user_id', 'pattern_key'])
    op.create_index('idx_weekly_error_report_user_week', 'weekly_error_reports', ['user_id', 'week_start'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_weekly_error_report_user_week', table_name='weekly_error_reports')
    op.drop_index('idx_error_signature_user_pattern', table_name='error_signatures')
    op.drop_index('idx_error_signature_user_skill', table_name='error_signatures')
    
    # Drop tables
    op.drop_table('weekly_error_reports')
    op.drop_table('error_signatures')
