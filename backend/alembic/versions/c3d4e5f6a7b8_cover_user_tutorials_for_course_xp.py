"""cover user_tutorials(tutorial_id) with user_id and xp_earned

Course leaderboards sum xp_earned per student across one course's tutorials.
With a plain index on tutorial_id, Postgres finds the matching rows and then
visits the heap for user_id and xp_earned. Including both in the index lets the
aggregate run entirely from it.

Measured at production scale (261k user_tutorials, 5.4k students, 4 courses):
24 ms -> 11 ms. Denormalising course_id onto user_tutorials was measured too
and rejected: only ~20% faster than the join, and it would store course_id in
two places, which is the same copy-drifts-from-source shape that caused the
leaderboard bugs this work exists to fix.

The covering index serves everything the plain tutorial_id index served, so it
replaces rather than joins it.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_INDEX = "idx_user_tutorials_tutorial"
NEW_INDEX = "idx_user_tutorials_tutorial_cover"


def upgrade() -> None:
    op.create_index(
        NEW_INDEX,
        "user_tutorials",
        ["tutorial_id"],
        unique=False,
        postgresql_include=["user_id", "xp_earned"],
    )
    op.drop_index(OLD_INDEX, table_name="user_tutorials")


def downgrade() -> None:
    op.create_index(OLD_INDEX, "user_tutorials", ["tutorial_id"], unique=False)
    op.drop_index(NEW_INDEX, table_name="user_tutorials")
