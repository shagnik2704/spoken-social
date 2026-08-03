"""
Reconcile student XP with their tutorial records — one-off legacy back-pay.
============================================================================

Why this exists (audit of 2026-08-02/03):

  * The Feb-May 2026 Swayam Plus cohort's forum posts set forum_asked /
    forum_answered via a radios-only sync that never recomputed xp_earned,
    leaving 3,246 tutorial rows underpaid (~49k XP). The code split is fixed
    (forum XP now awards at event time); this script settles the debt.
  * Independently, 37 of those students have xp_total sitting BELOW even the
    sum of their stored xp_earned rows (−1,945) — three ledgers, three
    answers. Increment-style repair would miss this, so this script uses
    SET semantics: recompute every row from its flags, then set each
    student's xp_total to the sum of their rows.

What it does (students only — admins/coordinators may hold manual XP that
tutorial rows can't reproduce, so they are never touched):

  1. user_tutorials.xp_earned := flag-sum (services/xp.py XP_MAP), where different
  2. users.xp_total          := Σ xp_earned over their rows, where different
  3. one xp_events row per adjusted student (source_type='reconciliation')
     so the change is auditable and visible in XP history
  4. users.level recalculated from the new total

Idempotent by construction: a second run finds zero differences.

Usage (inside the backend container):
    python scripts/reconcile_xp.py            # dry run — prints the plan, writes NOTHING
    python scripts/reconcile_xp.py --apply    # asks for confirmation, then writes

Run a backup first:  ./backup_db.sh --prod
After applying, restart the backend so the leaderboard reseeds from the new
totals:  docker compose restart backend
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import text
from database import SyncSessionLocal, DATABASE_URL
from services.xp import XP_MAP, _LEVELS

EVENT_SOURCE_TYPE = "reconciliation"
EVENT_SOURCE_ID = "legacy-forum-backpay-2026-08"

# Flag-sum expression built from the real XP_MAP so this script can never
# drift from services/xp.py.
FLAG_SUM_SQL = " + ".join(
    f"(CASE WHEN {col} THEN {xp} ELSE 0 END)" for col, xp in XP_MAP.items()
)

# Level expression built from the real thresholds.
LEVEL_CASE_SQL = "CASE " + " ".join(
    f"WHEN xp_total >= {threshold} THEN {level}" for threshold, level in _LEVELS
) + " ELSE 1 END"


def summarize(db):
    """Compute the full plan. Read-only."""
    rows = db.execute(text(f"""
        SELECT count(*) AS n
        FROM user_tutorials ut
        JOIN users u ON u.id = ut.user_id
        WHERE u.role = 'student'
          AND COALESCE(ut.xp_earned, 0) != ({FLAG_SUM_SQL})
    """)).scalar()

    users = db.execute(text(f"""
        WITH f AS (
            SELECT user_id, sum({FLAG_SUM_SQL}) AS fs
            FROM user_tutorials GROUP BY user_id
        )
        SELECT u.id, u.display_name, u.xp_total AS now,
               COALESCE(f.fs, 0) AS target,
               COALESCE(f.fs, 0) - u.xp_total AS delta
        FROM users u LEFT JOIN f ON f.user_id = u.id
        WHERE u.role = 'student' AND u.xp_total != COALESCE(f.fs, 0)
        ORDER BY COALESCE(f.fs, 0) - u.xp_total DESC
    """)).fetchall()

    return rows, users


def main():
    apply = "--apply" in sys.argv
    yes = "--yes" in sys.argv

    target = urlparse(DATABASE_URL)
    print(f"Database: {target.hostname or 'local'}:{target.port or 5432}{target.path}")
    print(f"Mode:     {'APPLY' if apply else 'DRY RUN (no writes)'}\n")

    db = SyncSessionLocal()
    try:
        row_count, users = summarize(db)
        gainers = [u for u in users if u.delta > 0]
        losers = [u for u in users if u.delta < 0]
        net = sum(u.delta for u in users)

        print(f"Tutorial rows where xp_earned != flag-sum : {row_count}")
        print(f"Students whose xp_total needs setting     : {len(users)}"
              f"  ({len(gainers)} gain, {len(losers)} lose)")
        print(f"Net XP change                             : {net:+d}\n")

        if users:
            print("Largest adjustments:")
            for u in users[:10]:
                print(f"   {u.display_name[:30]:<30} {u.now:>6} -> {u.target:>6}  ({u.delta:+d})")
            for u in losers:
                print(f"   {u.display_name[:30]:<30} {u.now:>6} -> {u.target:>6}  ({u.delta:+d})  [reduction]")

        if not apply:
            print("\nDry run only — nothing written. Re-run with --apply to execute.")
            return

        if row_count == 0 and not users:
            print("Nothing to reconcile — already consistent.")
            return

        if not yes:
            expected = (target.path or "/").lstrip("/")
            answer = input(f"\nType the database name ('{expected}') to apply: ").strip()
            if answer != expected:
                print("Aborted — name did not match. Nothing written.")
                return

        # 1. Rows: xp_earned := flag-sum (students only)
        r1 = db.execute(text(f"""
            UPDATE user_tutorials ut
            SET xp_earned = ({FLAG_SUM_SQL})
            FROM users u
            WHERE u.id = ut.user_id AND u.role = 'student'
              AND COALESCE(ut.xp_earned, 0) != ({FLAG_SUM_SQL})
        """))

        # 2. Audit trail BEFORE totals move, one event per adjusted student.
        #    course_id stays NULL like other pre-attribution historical events.
        db.execute(text(f"""
            WITH f AS (
                SELECT user_id, sum({FLAG_SUM_SQL}) AS fs
                FROM user_tutorials GROUP BY user_id
            )
            INSERT INTO xp_events (user_id, source_type, source_id, xp_delta, created_at)
            SELECT u.id, :st, :sid, COALESCE(f.fs, 0) - u.xp_total, NOW()
            FROM users u LEFT JOIN f ON f.user_id = u.id
            WHERE u.role = 'student' AND u.xp_total != COALESCE(f.fs, 0)
        """), {"st": EVENT_SOURCE_TYPE, "sid": EVENT_SOURCE_ID})

        # 3. Totals: xp_total := Σ xp_earned, and level from the new total.
        r3 = db.execute(text("""
            WITH f AS (
                SELECT user_id, sum(xp_earned) AS fs
                FROM user_tutorials GROUP BY user_id
            )
            UPDATE users u
            SET xp_total = f.fs
            FROM f
            WHERE f.user_id = u.id AND u.role = 'student'
              AND u.xp_total != f.fs
        """))
        # Students with XP but zero tutorial rows (none exist today; belt-and-braces
        # so the apply can never diverge from the plan summarize() printed).
        db.execute(text("""
            UPDATE users u SET xp_total = 0
            WHERE u.role = 'student' AND u.xp_total != 0
              AND NOT EXISTS (SELECT 1 FROM user_tutorials ut WHERE ut.user_id = u.id)
        """))
        db.execute(text(f"UPDATE users SET level = {LEVEL_CASE_SQL} WHERE role = 'student'"))

        db.commit()
        print(f"\nApplied: {r1.rowcount} rows recomputed, {r3.rowcount} totals set.")

        # 4. Verify from the database, not from our own bookkeeping.
        left_rows, left_users = summarize(db)
        if left_rows == 0 and not left_users:
            print("Verified: every student row and total now matches its flags. ✅")
            print("\nNow restart the backend so the leaderboard reseeds:")
            print("    docker compose restart backend")
        else:
            print(f"WARNING: {left_rows} rows / {len(left_users)} users still "
                  f"inconsistent — investigate before restarting.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
