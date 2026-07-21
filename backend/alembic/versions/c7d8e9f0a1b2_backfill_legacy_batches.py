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

THE ACTUAL HISTORY (confirmed with the team, 2026-07-21):

  - The FIRST Linux run (Feb-May 2026, the pre-batch cohort) was offered
    under the SWAYAM PLUS programme, since wound down.
  - The SECOND, currently running Linux is under FDP.
  - programme_courses only maps linux -> fdp because it was seeded after the
    second run began; it never knew about the Swayam Plus era. That is why
    any auto-resolution from programme_courses would mislabel this cohort.

So this migration attaches the orphaned enrollments to an explicit,
hand-written batch definition per course (LEGACY_BATCHES below) instead of
guessing. If orphans exist for a course with no entry in the map, it raises
rather than inventing history.

⚠️ TWO THINGS TO CHECK BEFORE RUNNING ON PRODUCTION:

1. Programme visibility gate. routes/programme.py filters
   Programme.is_active == True for BOTH students and admins. If swayam_plus
   has is_active = false in that database, this backfill fixes analytics but
   students still see an empty programme list. The migration prints a
   WARNING in that case; deciding whether to re-activate the programme is a
   product call, not something a migration should do silently.

2. Write lockout. dependencies.py:81 (check_batch_active) currently waves
   NULL batch_id through, so batch-less students can still record progress.
   After backfill their batch's end_date is past -> computed_status
   "inactive" -> progress writes carrying the batch id get 403. Verified
   correct for this cohort: last XP event 2026-05-31, quiet for ~7 weeks.
   If a cohort in LEGACY_BATCHES is still active, set its end date in the
   future.

Note: this file was revised after the beta rehearsal (which validated the
mechanics: orphan detection, batch creation, backfill, restored programme
join). Beta's rehearsal data was fully reverted, so editing in place only
affects databases that have not yet run c7d8e9f0a1b2 — i.e. production.

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


# ── The known pre-batch cohorts ─────────────────────────────────────────────
# One entry per course that has orphaned (batch_id IS NULL) enrollments.
# Named like real batches ("Feb-May 2026", cf. "Jan-Apr 2026" in models/batch.py)
# because they WERE real cohorts — nothing user-facing should say "legacy".
# End dates in the past make computed_status report "inactive" (archived).
LEGACY_BATCHES = {
    'linux': {
        'batch_id': 'linux-swayam-2026-feb',
        'programme_id': 'swayam_plus',   # the first Linux ran under Swayam Plus
        'name': 'Feb-May 2026',
        'start_date': '2026-02-01',
        'end_date': '2026-05-31',        # last recorded XP event of the cohort
    },
}
# ────────────────────────────────────────────────────────────────────────────


def upgrade() -> None:
    conn = op.get_bind()

    affected = conn.execute(sa.text(
        "SELECT course_id, COUNT(*) AS orphaned "
        "FROM user_courses WHERE batch_id IS NULL GROUP BY course_id"
    )).fetchall()

    if not affected:
        print("[legacy-batches] No batch-less enrollments. Nothing to do.")
        return

    # Refuse to invent history for cohorts nobody described.
    unknown = sorted(r.course_id for r in affected if r.course_id not in LEGACY_BATCHES)
    if unknown:
        raise RuntimeError(
            f"Orphaned enrollments found for course(s) with no LEGACY_BATCHES "
            f"entry: {', '.join(unknown)}. Add their real cohort history to "
            f"this migration before running it."
        )

    for row in affected:
        print(f"[legacy-batches] {row.course_id}: {row.orphaned} orphaned enrollments")

    affected_courses = {r.course_id for r in affected}
    for course_id, cfg in LEGACY_BATCHES.items():
        if course_id not in affected_courses:
            continue

        programme = conn.execute(
            sa.text("SELECT is_active FROM programmes WHERE id = :pid"),
            {"pid": cfg['programme_id']},
        ).fetchone()
        if programme is None:
            raise RuntimeError(
                f"Programme '{cfg['programme_id']}' does not exist in this "
                f"database — the backfill would leave '{course_id}' students "
                f"just as invisible as before. Seed the programme first."
            )
        if not programme.is_active:
            print(
                f"[legacy-batches] WARNING: programme '{cfg['programme_id']}' "
                f"has is_active=false. routes/programme.py hides inactive "
                f"programmes from students AND admins, so this backfill will "
                f"fix analytics but NOT restore the students' programme list. "
                f"Re-activating the programme is a separate product decision."
            )

        conn.execute(sa.text("""
            INSERT INTO batches
                (id, course_id, programme_id, name, start_date, end_date, status, created_at)
            VALUES
                (:bid, :cid, :pid, :name, :start, :end, 'active', NOW())
            ON CONFLICT (id) DO NOTHING
        """), {
            "bid": cfg['batch_id'], "cid": course_id, "pid": cfg['programme_id'],
            "name": cfg['name'], "start": cfg['start_date'], "end": cfg['end_date'],
        })

        conn.execute(sa.text(
            "UPDATE user_courses SET batch_id = :bid "
            "WHERE course_id = :cid AND batch_id IS NULL"
        ), {"bid": cfg['batch_id'], "cid": course_id})

    remaining = conn.execute(sa.text(
        "SELECT COUNT(*) FROM user_courses WHERE batch_id IS NULL"
    )).scalar()
    print(f"[legacy-batches] Done. Batch-less enrollments remaining: {remaining}")


def downgrade() -> None:
    # Only touches the exact batches this migration defines.
    conn = op.get_bind()
    for cfg in LEGACY_BATCHES.values():
        conn.execute(
            sa.text("UPDATE user_courses SET batch_id = NULL WHERE batch_id = :bid"),
            {"bid": cfg['batch_id']},
        )
        conn.execute(
            sa.text("DELETE FROM batches WHERE id = :bid"),
            {"bid": cfg['batch_id']},
        )
