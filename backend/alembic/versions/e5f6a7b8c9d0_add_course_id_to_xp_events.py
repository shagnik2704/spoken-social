"""add course_id to xp_events

Lets the daily-XP chart be course-scoped like every other metric. Nullable: existing
events pre-date this and their source_id doesn't reliably map to a course, so they stay
NULL (and simply won't appear in course-filtered views). All NEW events are tagged at the
write sites (update_tutorial, forum award/revoke).

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('xp_events', sa.Column('course_id', sa.String(length=50), nullable=True))
    op.create_foreign_key(
        'fk_xp_events_course', 'xp_events', 'courses', ['course_id'], ['id']
    )
    op.create_index('idx_xp_events_course', 'xp_events', ['course_id'])


def downgrade() -> None:
    op.drop_index('idx_xp_events_course', table_name='xp_events')
    op.drop_constraint('fk_xp_events_course', 'xp_events', type_='foreignkey')
    op.drop_column('xp_events', 'course_id')
