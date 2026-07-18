"""Add comprehensive grammar module tables

Revision ID: grammar_module_v1
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'grammar_module_v1'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to grammar_skills
    op.add_column('grammar_skills', sa.Column('module', sa.String(length=50), nullable=True))
    op.add_column('grammar_skills', sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'))
    op.add_column('grammar_skills', sa.Column('recent_performance', sa.JSON(), nullable=True))
    op.add_column('grammar_skills', sa.Column('last_reviewed', sa.DateTime(), nullable=True))
    
    # Add error_type column to grammar_mistakes
    op.add_column('grammar_mistakes', sa.Column('error_type', sa.String(length=50), nullable=True))
    
    # Create grammar_topics table
    op.create_table('grammar_topics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic_name', sa.String(length=100), nullable=False),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_in_module', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prerequisites', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create grammar_exercises table
    op.create_table('grammar_exercises',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('exercise_type', sa.String(length=50), nullable=False),
        sa.Column('question_data', sa.JSON(), nullable=False),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['grammar_topics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create grammar_attempts table
    op.create_table('grammar_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('user_answer', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('time_spent', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['exercise_id'], ['grammar_exercises.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['grammar_skills.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create grammar_notes table
    op.create_table('grammar_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('mistake_pattern', sa.Text(), nullable=True),
        sa.Column('correction', sa.Text(), nullable=True),
        sa.Column('example', sa.Text(), nullable=True),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['grammar_skills.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create grammar_learning_history table
    op.create_table('grammar_learning_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['grammar_skills.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_grammar_skill_module', 'grammar_skills', ['module'])
    op.create_index('idx_grammar_topic_module', 'grammar_topics', ['module'])
    op.create_index('idx_grammar_exercise_topic', 'grammar_exercises', ['topic_id'])
    op.create_index('idx_grammar_attempt_user_exercise', 'grammar_attempts', ['user_id', 'exercise_id'])
    op.create_index('idx_grammar_note_user_skill', 'grammar_notes', ['user_id', 'skill_id'])
    op.create_index('idx_grammar_history_user_skill', 'grammar_learning_history', ['user_id', 'skill_id'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_grammar_history_user_skill')
    op.drop_index('idx_grammar_note_user_skill')
    op.drop_index('idx_grammar_attempt_user_exercise')
    op.drop_index('idx_grammar_exercise_topic')
    op.drop_index('idx_grammar_topic_module')
    op.drop_index('idx_grammar_skill_module')
    
    # Drop tables in reverse order
    op.drop_table('grammar_learning_history')
    op.drop_table('grammar_notes')
    op.drop_table('grammar_attempts')
    op.drop_table('grammar_exercises')
    op.drop_table('grammar_topics')
    
    # Drop columns from existing tables
    op.drop_column('grammar_mistakes', 'error_type')
    op.drop_column('grammar_skills', 'last_reviewed')
    op.drop_column('grammar_skills', 'recent_performance')
    op.drop_column('grammar_skills', 'confidence')
    op.drop_column('grammar_skills', 'module')