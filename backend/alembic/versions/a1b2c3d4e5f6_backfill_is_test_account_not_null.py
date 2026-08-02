"""backfill users.is_test_account and make it NOT NULL

`is_test_account` was added as a nullable column by cf9a1ff8d355, with only a
Python-side default (models/user.py). Rows created before that migration — and
any created by raw SQL / bulk import since — therefore hold NULL rather than
false.

Every eligibility filter in the codebase is written as

    User.is_test_account != True

which SQLAlchemy renders as SQL `is_test_account != true`. Under three-valued
logic `NULL != true` is NULL, not true, so **every NULL row is silently
excluded**. NULL does not mean "unknown test status" here; it means "this row
predates the column". The filters are dropping real students.

Measured on prod (2026-08-02) before this migration:

  * 2,444 of 5,446 students hold NULL (the Feb-Mar 2026 legacy import).
    All 2,444 have an email, a college, and user_tutorials progress rows.
  * 0 rows anywhere hold is_test_account = true. The filter is currently
    excluding 2,444 real students and 0 actual test accounts.
  * 19 colleges render completely empty on their coordinator dashboard
    (e.g. Ambalika Institute: 825 enrolled, 0 visible).
  * 77 of the true top-100 students are missing from the public leaderboard,
    which pads the gap with 0-XP accounts.

The fix is applied at the schema level rather than by rewriting ~15 call sites:
once NULL cannot exist, `!= True` is correct everywhere by construction, and a
future bulk import cannot silently reintroduce the bug. Call sites may still be
migrated to `.isnot(True)` for clarity, but they are no longer load-bearing.

Idempotent: the UPDATE matches nothing on a database that is already clean, and
the ALTERs are no-ops if the constraint is already in place.

Revision ID: a1b2c3d4e5f6
Revises: b3c4d5e6f7a8
Create Date: 2026-08-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Report what is about to change, broken down by role — the student number is
    # the one that drives leaderboard/coordinator visibility, but coordinator and
    # admin rows carry NULL too and are filtered by the same expression in
    # routes/admin.py.
    rows = conn.execute(sa.text("""
        SELECT role, count(*) AS n
        FROM users
        WHERE is_test_account IS NULL
        GROUP BY role
        ORDER BY role
    """)).fetchall()

    if rows:
        detail = ", ".join(f"{r.role}: {r.n}" for r in rows)
        print(f"[is-test-account] Backfilling NULL -> false ({detail}).")
    else:
        print("[is-test-account] No NULL rows — backfill is a no-op.")

    conn.execute(sa.text(
        "UPDATE users SET is_test_account = false WHERE is_test_account IS NULL"
    ))

    # server_default (not just the Python-side default) so raw SQL inserts and
    # future bulk imports cannot reintroduce NULL.
    op.alter_column(
        'users', 'is_test_account',
        existing_type=sa.Boolean(),
        server_default=sa.false(),
        nullable=False,
    )

    print("[is-test-account] users.is_test_account is now NOT NULL DEFAULT false.")


def downgrade() -> None:
    # Reverts the constraint only. The backfilled false values are intentionally
    # NOT restored to NULL: which rows were NULL is not recorded anywhere, and
    # NULL was a data defect rather than meaningful state. Re-running upgrade()
    # after this downgrade is a clean no-op.
    op.alter_column(
        'users', 'is_test_account',
        existing_type=sa.Boolean(),
        server_default=None,
        nullable=True,
    )
