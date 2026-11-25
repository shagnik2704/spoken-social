"""add reading_done to user_tutorials

Separates Reading notes completion (`reading_done`) from Watch video (`watched`)
so watching a tutorial video no longer auto-completes Reading notes.

Revision ID: f8c9d0e1a2b3
Revises: e4a7c9d2b815
Create Date: 2026-11-25 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8c9d0e1a2b3'
down_revision: Union[str, Sequence[str], None] = 'e4a7c9d2b815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_tutorials',
        sa.Column('reading_done', sa.Boolean(), server_default='false', nullable=True),
    )
    # Backfill courses without an embedded video (e.g. Personality Dev), where
    # clicking "Mark Complete" on Reading previously set `watched = true`.
    op.execute("""
        UPDATE user_tutorials ut
           SET reading_done = true
          FROM tutorials t
          LEFT JOIN tutorial_contents tc ON tc.tutorial_id = t.id
         WHERE t.id = ut.tutorial_id
           AND ut.watched = true
           AND COALESCE(NULLIF(tc.video_url, ''), NULLIF(t.video_url, '')) IS NULL
    """)


def downgrade() -> None:
    op.drop_column('user_tutorials', 'reading_done')
