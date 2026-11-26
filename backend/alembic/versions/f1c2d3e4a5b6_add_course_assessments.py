"""add course assessments, course guide and tutorial watch page url

Labs and capstones span several tutorials and are graded by evaluators, so they
live at course level with their own submissions instead of riding on one
tutorial's assignment flag. They carry no XP, which keeps the XP invariant
(users.xp_total equals the sum of user_tutorials.xp_earned) untouched.

courses.guide holds a course's own learner-facing guide (modules, week plan,
marks, safety rules, live sessions), parsed from its learner pack.

Revision ID: f1c2d3e4a5b6
Revises: b2c3d4e5f6a8
Create Date: 2026-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f1c2d3e4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tutorials', sa.Column('video_page_url', sa.Text(), nullable=True))
    op.add_column('courses', sa.Column('guide', postgresql.JSONB(), nullable=True))

    op.create_table(
        'course_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('course_id', sa.String(50), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key', sa.String(50), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('number', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('week_due', sa.Integer(), nullable=False),
        sa.Column('covers', sa.String(255), nullable=True),
        sa.Column('instructions_markdown', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('course_id', 'key', name='uq_course_assessment_key'),
    )
    op.create_index('idx_course_assessments_course', 'course_assessments', ['course_id'])

    op.create_table(
        'user_assessment_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('course_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_text', sa.Text(), nullable=False),
        sa.Column('link_url', sa.Text(), nullable=True),
        sa.Column('file_url', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='submitted'),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('user_id', 'assessment_id', name='uq_user_assessment_submission'),
    )
    op.create_index('idx_user_assessment_submissions_user', 'user_assessment_submissions', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_user_assessment_submissions_user', table_name='user_assessment_submissions')
    op.drop_table('user_assessment_submissions')
    op.drop_index('idx_course_assessments_course', table_name='course_assessments')
    op.drop_table('course_assessments')
    op.drop_column('courses', 'guide')
    op.drop_column('tutorials', 'video_page_url')
