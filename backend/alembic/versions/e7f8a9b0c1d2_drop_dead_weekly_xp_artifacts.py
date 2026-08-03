"""drop leaderboard_weekly and users.xp_last_week

Both were attempts at weekly XP that never got a writer: the table has always
held 0 rows and the column has always held 0 for every user. Weekly and monthly
boards are now computed from xp_events (services/leaderboard.py), so neither
will ever be filled.

Safe to drop rather than backfill — verified on production that no row has a
non-zero xp_last_week and leaderboard_weekly is empty, so nothing is lost.

Revision ID: e7f8a9b0c1d2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    rows = conn.execute(sa.text("SELECT count(*) FROM leaderboard_weekly")).scalar()
    dirty = conn.execute(sa.text("SELECT count(*) FROM users WHERE xp_last_week != 0")).scalar()
    if rows or dirty:
        raise RuntimeError(
            f"refusing to drop: leaderboard_weekly has {rows} rows and "
            f"{dirty} users have a non-zero xp_last_week — investigate first"
        )

    op.drop_table("leaderboard_weekly")
    op.drop_column("users", "xp_last_week")
    print("[drop-weekly] removed leaderboard_weekly and users.xp_last_week")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("xp_last_week", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "leaderboard_weekly",
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("course_id", sa.String(length=50), nullable=False, server_default="__all__"),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("xp_week", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("week_start", "course_id", "user_id"),
    )
    op.create_index(
        "idx_leaderboard_week_start_course",
        "leaderboard_weekly",
        ["week_start", "course_id", "rank"],
    )
