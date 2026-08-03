"""XP integrity checks.

These are the invariants that were silently violated in production for roughly
four months: 3,247 tutorial rows disagreed with their own flags and 37 students
held a total below the sum of their rows, together hiding ~49k XP of unpaid
work. Nothing was watching, so it surfaced during an audit rather than the next
morning.

Every check is expressed as "how many rows are wrong", so a healthy system
reports zeros. `xp_drift` is signed and says how much XP would move if the
system were reconciled now — positive means students are owed.

The expressions are built from services.xp.XP_MAP and _LEVELS rather than
hardcoded, so changing the earning rules cannot leave the checker asserting the
old ones.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.forum import VERIFICATION_HOURS
from services.xp import XP_MAP, _LEVELS

FLAG_SUM = " + ".join(
    f"(CASE WHEN {col} THEN {xp} ELSE 0 END)" for col, xp in XP_MAP.items()
)

# Forum XP is held until a post survives the verification window, so between the
# radio flipping and the worker paying, xp_earned legitimately sits below the
# flag sum. Subtracting still-pending forum XP is what stops that showing up as
# a nightly violation.
#
# The exemption is scoped to the window on purpose: an activity that ages past
# it without being awarded stops being excused and the invariant fires, so a
# worker that has stopped running surfaces here rather than staying invisible.
PENDING_FORUM_XP = f"""
    COALESCE((
        SELECT (CASE WHEN ut.forum_asked
                      AND bool_or(fa.activity_type = 'question') THEN {XP_MAP['forum_asked']} ELSE 0 END)
             + (CASE WHEN ut.forum_answered
                      AND bool_or(fa.activity_type = 'answer') THEN {XP_MAP['forum_answered']} ELSE 0 END)
        FROM forum_activities fa
        WHERE fa.user_id = ut.user_id
          AND fa.tutorial_id = ut.tutorial_id
          AND fa.xp_awarded = false
          AND fa.deleted_on_forum = false
          AND fa.posted_at > NOW() - INTERVAL '{VERIFICATION_HOURS} hours'
    ), 0)
"""
EXPECTED_XP = f"(({FLAG_SUM}) - ({PENDING_FORUM_XP}))"
LEVEL_CASE = (
    "CASE "
    + " ".join(f"WHEN xp_total >= {t} THEN {lvl}" for t, lvl in _LEVELS)
    + " ELSE 1 END"
)
XP_STEP = min(XP_MAP.values())
MAX_TUTORIAL_XP = sum(XP_MAP.values())


async def check_xp_integrity(db: AsyncSession) -> dict:
    """Count violations of every XP invariant. All-zero means healthy."""
    row = (await db.execute(text(f"""
        SELECT
          (SELECT count(*) FROM user_tutorials ut JOIN users u ON u.id = ut.user_id
             WHERE u.role = 'student'
               AND COALESCE(ut.xp_earned, 0) != {EXPECTED_XP}
          ) AS tutorial_rows_off,

          (SELECT count(*) FROM users u
             LEFT JOIN (SELECT user_id, sum(xp_earned) AS s FROM user_tutorials GROUP BY user_id) t
               ON t.user_id = u.id
             WHERE u.role = 'student' AND u.xp_total != COALESCE(t.s, 0)
          ) AS user_totals_off,

          (SELECT COALESCE(sum(COALESCE(t.s, 0) - u.xp_total), 0) FROM users u
             LEFT JOIN (SELECT ut.user_id, sum({EXPECTED_XP}) AS s
                          FROM user_tutorials ut GROUP BY ut.user_id) t
               ON t.user_id = u.id
             WHERE u.role = 'student' AND u.xp_total != COALESCE(t.s, 0)
          ) AS xp_drift,

          (SELECT count(*) FROM users WHERE role = 'student' AND level != ({LEVEL_CASE})
          ) AS levels_off,

          (SELECT count(*) FROM users
             WHERE role = 'student' AND (xp_total < 0 OR xp_total % {XP_STEP} != 0)
          ) AS impossible_totals,

          (SELECT count(*) FROM user_tutorials
             WHERE COALESCE(xp_earned, 0) < 0 OR COALESCE(xp_earned, 0) > {MAX_TUTORIAL_XP}
          ) AS impossible_rows,

          (SELECT count(*) FROM users WHERE is_test_account IS NULL) AS null_test_flags
    """))).mappings().one()

    result = {k: int(v) for k, v in row.items()}
    result["healthy"] = all(v == 0 for v in result.values())
    return result


async def find_drifted_users(db: AsyncSession, limit: int = 20) -> list[dict]:
    """The students behind a non-zero xp_drift, worst first — so an alert can
    name names instead of only a count."""
    rows = (await db.execute(text(f"""
        WITH implied AS (
            SELECT ut.user_id, sum({EXPECTED_XP}) AS xp FROM user_tutorials ut GROUP BY ut.user_id
        )
        SELECT u.id::text AS id, u.display_name AS name, u.xp_total,
               COALESCE(i.xp, 0) AS implied,
               COALESCE(i.xp, 0) - u.xp_total AS drift
        FROM users u LEFT JOIN implied i ON i.user_id = u.id
        WHERE u.role = 'student' AND u.xp_total != COALESCE(i.xp, 0)
        ORDER BY abs(COALESCE(i.xp, 0) - u.xp_total) DESC
        LIMIT :limit
    """), {"limit": limit})).mappings().all()
    return [dict(r) for r in rows]
