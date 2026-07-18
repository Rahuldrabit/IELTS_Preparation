"""Add Cognitive Telemetry Engine tables.

Revision ID: 003
Revises: 002
Create Date: 2026-07-18

Tables:
  - telemetry_sessions
  - telemetry_summaries
  - attention_scores
  - question_behavior
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Telemetry Sessions
    op.create_table(
        'telemetry_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('backend_session_id', sa.Integer(), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('skill', sa.String(20), nullable=False),
        sa.Column('calibration_accuracy', sa.Float(), nullable=True),
        sa.Column('gaze_enabled', sa.Boolean(), default=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_telemetry_sessions_user', 'telemetry_sessions', ['user_id'])
    op.create_index('idx_telemetry_sessions_backend', 'telemetry_sessions', ['backend_session_id'])

    # Telemetry Summaries
    op.create_table(
        'telemetry_summaries',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('telemetry_session_id', sa.Integer(), sa.ForeignKey('telemetry_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('paragraph_time', sa.JSON(), nullable=True),
        sa.Column('fixation_count', sa.Integer(), default=0),
        sa.Column('regression_count', sa.Integer(), default=0),
        sa.Column('skip_rate', sa.Float(), default=0.0),
        sa.Column('blink_rate', sa.Float(), default=0.0),
        sa.Column('focus_score', sa.Float(), default=0.0),
        sa.Column('avg_fixation_ms', sa.Float(), default=0.0),
        sa.Column('reading_speed_wpm', sa.Float(), default=0.0),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_telemetry_summaries_session', 'telemetry_summaries', ['telemetry_session_id'])

    # Attention Scores
    op.create_table(
        'attention_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('telemetry_session_id', sa.Integer(), sa.ForeignKey('telemetry_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('overall_attention', sa.Float(), default=0.0),
        sa.Column('scanning_efficiency', sa.Float(), default=0.0),
        sa.Column('regression_severity', sa.Float(), default=0.0),
        sa.Column('time_management', sa.Float(), default=0.0),
        sa.Column('focus_stability', sa.Float(), default=0.0),
        sa.Column('computed_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_attention_scores_session', 'attention_scores', ['telemetry_session_id'])

    # Question Behavior
    op.create_table(
        'question_behavior',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('telemetry_session_id', sa.Integer(), sa.ForeignKey('telemetry_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('fixation_count', sa.Integer(), default=0),
        sa.Column('regression_count', sa.Integer(), default=0),
        sa.Column('time_spent_ms', sa.Integer(), default=0),
        sa.Column('paragraph_visits', sa.JSON(), nullable=True),
        sa.Column('confidence_signal', sa.String(20), nullable=True),
        sa.Column('answer_correct', sa.Boolean(), nullable=True),
    )
    op.create_index('idx_question_behavior_session', 'question_behavior', ['telemetry_session_id'])


def downgrade() -> None:
    op.drop_table('question_behavior')
    op.drop_table('attention_scores')
    op.drop_table('telemetry_summaries')
    op.drop_table('telemetry_sessions')
