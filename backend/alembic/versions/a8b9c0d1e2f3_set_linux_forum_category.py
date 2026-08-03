"""set the Linux course's forum_category

Linux was the only course with no forum_category, so no incoming forum event
could ever resolve to it by category. Events still mapped, but only via
find_tutorial_by_name's last-resort match of the tutorial title across every
course — which works solely because titles happen to be unique platform-wide
today, and would silently attribute XP to the wrong course the moment two
courses shared one.

'Linux-New' is what the forum actually sends: of the recorded events in
forum_activities, the three most recent all carry that category (an older one
carries plain 'Linux'). Matching is normalised for hyphens, spacing and case
now, so 'Linux-New', 'Linux New' and 'linux new' all resolve; bare 'Linux'
would not, and falls back to the title match as it does today.

Revision ID: a8b9c0d1e2f3
Revises: e7f8a9b0c1d2
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a8b9c0d1e2f3'
down_revision: Union[str, Sequence[str], None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORY = "Linux-New"


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "UPDATE courses SET forum_category = :cat "
            "WHERE id = 'linux' AND forum_category IS NULL"
        ),
        {"cat": CATEGORY},
    )
    if result.rowcount:
        print(f"[forum-category] linux -> {CATEGORY!r}")
    else:
        print("[forum-category] linux already has a category — left untouched")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE courses SET forum_category = NULL "
            "WHERE id = 'linux' AND forum_category = :cat"
        ),
        {"cat": CATEGORY},
    )
