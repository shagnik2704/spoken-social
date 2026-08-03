"""index users(college_id, xp_total desc) for college-scoped leaderboards

Without it, a college board filters on college_id and then sorts the matches by
XP. The composite index seeks to the college and reads rows already in rank
order, so the LIMIT stops early — the same shape that makes the global board
cost the same at 5k students as at 100k.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "idx_users_college_xp"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        "users",
        ["college_id", sa.text("xp_total DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="users")
