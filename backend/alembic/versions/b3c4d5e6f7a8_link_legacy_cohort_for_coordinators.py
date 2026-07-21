"""link legacy cohort junction rows for coordinator visibility

Companion to c7d8e9f0a1b2 (backfill legacy batches). That migration restores
the legacy Swayam Plus Linux cohort for students (batch.programme_id drives
their programme list) and admins (/comparison-metrics infers course->programme
links from batches). Coordinators are the remaining blind spot: their
programme dropdown (routes/programme.py:76-92) joins

    programme_courses  (programme offers course)
    college_courses    (college runs course under programme)

and BOTH still say Linux is FDP-only, because both were seeded during the
FDP era. A coordinator whose college ran the Feb-May 2026 Swayam Plus cohort
therefore cannot select Swayam Plus to look at it.

This migration adds the missing history:

  1. programme_courses: (swayam_plus, linux)
  2. college_courses:   (college, linux, swayam_plus) for every college that
     actually had students in the legacy batch — derived from the users
     attached to it by c7d8e9f0a1b2, not from a hand-written college list.

Accepted side effect: the landing-page course selector
(routes/course.py:96 /all-with-batches?programme_id=swayam_plus) will now
list Linux under Swayam Plus. Verified safe: line 114 filters batches by
programme, so only the archived "Feb-May 2026" batch appears there — the
current FDP batch never shows under Swayam Plus, and the archived batch's
is_active=false flag lets the frontend exclude it from enrollment.

Ordering: must run AFTER c7d8e9f0a1b2 (it reads the legacy batch's members).
Alembic guarantees this via down_revision. On a database where the legacy
batch does not exist (e.g. beta, where the rehearsal was reverted), this is
a clean no-op.

Revision ID: b3c4d5e6f7a8
Revises: c7d8e9f0a1b2
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Mirrors LEGACY_BATCHES in c7d8e9f0a1b2 (alembic migrations are not
# importable from each other, so the ids are restated here).
LEGACY_LINKS = {
    'linux': {
        'batch_id': 'linux-swayam-2026-feb',
        'programme_id': 'swayam_plus',
    },
}


def upgrade() -> None:
    conn = op.get_bind()

    for course_id, cfg in LEGACY_LINKS.items():
        batch = conn.execute(
            sa.text("SELECT id FROM batches WHERE id = :bid"),
            {"bid": cfg['batch_id']},
        ).fetchone()
        if batch is None:
            print(f"[legacy-links] Batch {cfg['batch_id']} not present — nothing to link.")
            continue

        conn.execute(sa.text("""
            INSERT INTO programme_courses (programme_id, course_id)
            VALUES (:pid, :cid)
            ON CONFLICT DO NOTHING
        """), {"pid": cfg['programme_id'], "cid": course_id})

        # enabled_at is set explicitly: the model default is Python-side only,
        # so raw SQL inserts would otherwise leave it NULL.
        result = conn.execute(sa.text("""
            INSERT INTO college_courses (college_id, course_id, programme_id, enabled_at)
            SELECT DISTINCT u.college_id, :cid, :pid, NOW()
            FROM user_courses uc
            JOIN users u ON u.id = uc.user_id
            WHERE uc.batch_id = :bid
              AND u.college_id IS NOT NULL
            ON CONFLICT DO NOTHING
        """), {"cid": course_id, "pid": cfg['programme_id'], "bid": cfg['batch_id']})

        print(
            f"[legacy-links] {course_id} -> {cfg['programme_id']}: "
            f"programme link ensured, {result.rowcount} college link(s) added."
        )


def downgrade() -> None:
    # Caveat: removes ALL (programme, course) junction rows for the pairs in
    # LEGACY_LINKS, including any that existed before this migration. As of
    # 2026-07-21 no such rows predate it on any environment (the swayam_plus
    # <-> linux link is exactly what was missing), so this is a clean inverse.
    conn = op.get_bind()
    for course_id, cfg in LEGACY_LINKS.items():
        conn.execute(sa.text(
            "DELETE FROM college_courses WHERE course_id = :cid AND programme_id = :pid"
        ), {"cid": course_id, "pid": cfg['programme_id']})
        conn.execute(sa.text(
            "DELETE FROM programme_courses WHERE course_id = :cid AND programme_id = :pid"
        ), {"cid": course_id, "pid": cfg['programme_id']})
