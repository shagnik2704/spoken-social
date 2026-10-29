"""add learner pack tables and course ui_layout

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-10-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

revision: str = 'b9c0d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add ui_layout to courses table
    op.add_column(
        'courses',
        sa.Column('ui_layout', sa.String(length=50), nullable=False, server_default='standard_tracker')
    )

    # 2. Create tutorial_contents table
    op.create_table(
        'tutorial_contents',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('tutorial_id', PG_UUID(as_uuid=True), sa.ForeignKey('tutorials.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('reading_title', sa.String(length=255), nullable=False),
        sa.Column('reading_markdown', sa.Text(), nullable=False),
        sa.Column('reading_time_minutes', sa.Integer(), server_default='15'),
        sa.Column('try_it_instructions', sa.Text(), nullable=False),
        sa.Column('reflection_prompt', sa.Text(), nullable=False),
        sa.Column('reflection_min_sentences', sa.Integer(), server_default='3'),
        sa.Column('key_terms', JSONB(), server_default='[]'),
        sa.Column('read_more', JSONB(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_tutorial_contents_tutorial', 'tutorial_contents', ['tutorial_id'])

    # 3. Create quiz_questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('tutorial_id', PG_UUID(as_uuid=True), sa.ForeignKey('tutorials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options', JSONB(), nullable=False),
        sa.Column('correct_option', sa.String(length=5), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('tutorial_id', 'question_number', name='uq_tutorial_quiz_question'),
    )
    op.create_index('idx_quiz_questions_tutorial', 'quiz_questions', ['tutorial_id'])

    # 4. Create user_reflections table
    op.create_table(
        'user_reflections',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', PG_UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tutorial_id', PG_UUID(as_uuid=True), sa.ForeignKey('tutorials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reflection_text', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), server_default='0'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'tutorial_id', name='uq_user_tutorial_reflection'),
    )
    op.create_index('idx_user_reflections_user', 'user_reflections', ['user_id'])

    # 5. Create user_quiz_attempts table
    op.create_table(
        'user_quiz_attempts',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', PG_UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tutorial_id', PG_UUID(as_uuid=True), sa.ForeignKey('tutorials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('total_questions', sa.Integer(), server_default='5'),
        sa.Column('submitted_answers', JSONB(), nullable=False),
        sa.Column('passed', sa.Boolean(), server_default='true'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'tutorial_id', name='uq_user_tutorial_quiz'),
    )
    op.create_index('idx_user_quiz_attempts_user', 'user_quiz_attempts', ['user_id'])

    # 6. Create user_habit_log_checkins table
    op.create_table(
        'user_habit_log_checkins',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', PG_UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.String(length=50), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('log_type', sa.String(length=50), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('checkin_date', sa.Date(), nullable=False),
        sa.Column('summary_reflection', sa.Text(), nullable=True),
        sa.Column('summary_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'course_id', 'log_type', 'day_number', name='uq_user_habit_day'),
    )
    op.create_index('idx_user_habit_checkins', 'user_habit_log_checkins', ['user_id', 'course_id', 'log_type'])


def downgrade() -> None:
    op.drop_table('user_habit_log_checkins')
    op.drop_table('user_quiz_attempts')
    op.drop_table('user_reflections')
    op.drop_table('quiz_questions')
    op.drop_table('tutorial_contents')
    op.drop_column('courses', 'ui_layout')
