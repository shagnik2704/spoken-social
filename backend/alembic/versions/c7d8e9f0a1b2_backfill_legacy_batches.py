"""backfill legacy batches for pre-batch enrollments

The batches table was introduced in cf9a1ff8d355 (2026-05-22). That migration
added user_courses.batch_id as nullable but never backfilled it, so every
enrollment created before that date still has batch_id IS NULL.

Those enrollments are invisible to any query that INNER JOINs batches:

  - routes/programme.py:99  — a student whose enrollments are all batch-less
                              gets an EMPTY programme list.
  - routes/course.py:91     — same, when ?programme_id= is supplied.
  - routes/admin.py:1698    — excluded from /comparison-metrics.

Coordinator and admin default views are unaffected: their batch filters are
conditional (`if batch_id:`), so batch-less students still appear there.

This migration creates one synthetic "<course>-legacy" batch per affected
course and points the orphaned enrollments at it.

⚠️ READ BEFORE RUNNING — this changes write permissions.

dependencies.py:81 (check_batch_active) short-circuits on a falsy batch_id:

    if not batch_id:
        return  # Assume active if no batch specified (backward compatibility)

So batch-less students can currently PUT tutorial progress. Once they belong
to a batch whose end_date has passed, computed_status becomes "inactive" and
that same endpoint returns 403.

  - Cohort genuinely finished  -> keep LEGACY_END_DATE in the past (default).
    Archiving it is the correct, intended behaviour.
  - Anyone still working through the course -> set LEGACY_END_DATE to a future
    date, otherwise you will lock 2,447 Linux students out of recording
    progress.

Confirm with the activity check in the docstring of _affected_counts() below
before applying to production.

Revision ID: c7d8e9f0a1b2
Revises: e5f6a7b8c9d0
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Tunables ────────────────────────────────────────────────────────────────
# Best-known window for the pre-batch cohort.
#
# LEGACY_END_DATE is set from the last recorded activity of a batch-less student
# (max xp_events.created_at = 2026-05-31), NOT from the date the batches table
# landed (2026-05-22) — students kept working for nine days after the schema
# change. The window has to contain its own cohort's activity.
#
# Verified quiet for ~7 weeks as of 2026-07-21, so archiving is correct here.
LEGACY_START_DATE = '2026-02-01'
LEGACY_END_DATE = '2026-05-31'   # past -> batch archives -> progress writes 403
LEGACY_NAME = 'Legacy (pre-batch)'
LEGACY_SUFFIX = '-legacy'
# ────────────────────────────────────────────────────────────────────────────


def _affected_counts(conn) -> list:
    """Report what this migration is about to touch.

    Equivalent standalone check, if you want to look before migrating:

        SELECT course_id, COUNT(*) AS orphaned
        FROM user_courses WHERE batch_id IS NULL
        GROUP BY course_id;
    """
    return conn.execute(sa.text(
        "SELECT course_id, COUNT(*) AS orphaned "
        "FROM user_courses WHERE batch_id IS NULL GROUP BY course_id"
    )).fetchall()


def upgrade() -> None:
    conn = op.get_bind()

    affected = _affected_counts(conn)
    if not affected:
        print("[legacy-batches] No batch-less enrollments. Nothing to do.")
        return
    for row in affected:
        print(f"[legacy-batches] {row.course_id}: {row.orphaned} orphaned enrollments")

    # One synthetic batch per affected course.
    #
    # programme_id MUST resolve to a real programme or this migration is
    # pointless: routes/programme.py joins Batch -> Programme, so a NULL
    # programme_id would leave these students just as invisible as before.
    # Prefer the course's programme_courses link, else borrow it from an
    # existing batch of the same course.
    op.execute(sa.text(f"""
        INSERT INTO batches
            (id, course_id, programme_id, name, start_date, end_date, status, created_at)
        SELECT
            uc.course_id || '{LEGACY_SUFFIX}',
            uc.course_id,
            COALESCE(
                (SELECT pc.programme_id FROM programme_courses pc
                  WHERE pc.course_id = uc.course_id
                  ORDER BY pc.programme_id LIMIT 1),
                (SELECT b.programme_id FROM batches b
                  WHERE b.course_id = uc.course_id AND b.programme_id IS NOT NULL
                  LIMIT 1)
            ),
            '{LEGACY_NAME}',
            DATE '{LEGACY_START_DATE}',
            DATE '{LEGACY_END_DATE}',
            'active',
            NOW()
        FROM user_courses uc
        WHERE uc.batch_id IS NULL
        GROUP BY uc.course_id
        ON CONFLICT (id) DO NOTHING
    """))

    # Fail loudly rather than silently half-fixing: a NULL programme_id here
    # means the student would still see an empty programme list.
    orphan_programmes = conn.execute(sa.text(f"""
        SELECT id FROM batches
        WHERE id LIKE '%{LEGACY_SUFFIX}' AND programme_id IS NULL
    """)).fetchall()
    if orphan_programmes:
        ids = ', '.join(r.id for r in orphan_programmes)
        raise RuntimeError(
            f"Could not resolve a programme_id for: {ids}. Seed programme_courses "
            f"for those courses first, or this backfill will not restore visibility."
        )

    op.execute(sa.text(f"""
        UPDATE user_courses
        SET batch_id = course_id || '{LEGACY_SUFFIX}'
        WHERE batch_id IS NULL
    """))

    remaining = conn.execute(sa.text(
        "SELECT COUNT(*) FROM user_courses WHERE batch_id IS NULL"
    )).scalar()
    print(f"[legacy-batches] Done. Batch-less enrollments remaining: {remaining}")


def downgrade() -> None:
    # Only touches rows this migration created — matched by the id suffix.
    op.execute(sa.text(f"""
        UPDATE user_courses SET batch_id = NULL
        WHERE batch_id LIKE '%{LEGACY_SUFFIX}'
    """))
    op.execute(sa.text(f"""
        DELETE FROM batches WHERE id LIKE '%{LEGACY_SUFFIX}'
    """))
