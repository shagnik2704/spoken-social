"""add activity_done to user_tutorials

The learner pack's private notebook activity used to add 5 XP straight to
users.xp_total while recording completion on minitask_opted, a flag outside
XP_MAP. Its XP never reached user_tutorials.xp_earned, so course leaderboards
missed it and the "total equals sum of rows" invariant broke for every student
who completed one.

activity_done is now an XP_MAP flag. The backfill marks it for rows that were
paid through the old path and adds that XP to the row only: the students'
totals already include it, so this closes the gap without paying anyone twice.

Revision ID: e4a7c9d2b815
Revises: 758114377162
Create Date: 2026-11-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e4a7c9d2b815'
down_revision: Union[str, Sequence[str], None] = '758114377162'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACTIVITY_XP = 5


def upgrade() -> None:
    op.add_column('user_tutorials', sa.Column('activity_done', sa.Boolean(), server_default='false', nullable=True))
    op.execute(f"""
        UPDATE user_tutorials ut
           SET activity_done = true,
               xp_earned = COALESCE(ut.xp_earned, 0) + {ACTIVITY_XP}
         WHERE ut.minitask_opted
           AND EXISTS (
               SELECT 1 FROM xp_events e
                WHERE e.user_id = ut.user_id
                  AND e.source_id = ut.tutorial_id::text
                  AND e.source_type = 'activity_completion'
           )
    """)


def downgrade() -> None:
    op.execute(f"""
        UPDATE user_tutorials
           SET xp_earned = GREATEST(COALESCE(xp_earned, 0) - {ACTIVITY_XP}, 0),
               minitask_opted = true
         WHERE activity_done
    """)
    op.drop_column('user_tutorials', 'activity_done')
