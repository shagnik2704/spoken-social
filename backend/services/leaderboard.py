"""
Leaderboard service — the single definition of what a leaderboard IS.

Replaces the Redis mirror in leaderboard_cache.py. That mirror was a second copy
of XP maintained by hand on every write path, and every leaderboard bug in the
2026-08 audit was a coherence failure between it and Postgres
(see docs/leaderboard-cache-coherence.md). Serving from Postgres removes the
copy, and therefore the bug class: measured 0.11 ms for the top-100 index scan
at 5,446 students, and the same 0.11 ms at 100,000 (a LIMIT on a descending
index never looks past the page).

Serving from SQL is also what makes scoping tractable. A scope here is a WHERE
clause; in Redis it would be a separate sorted set per college / course / batch
/ window, each needing a write on every XP change — thousands of keys to keep
coherent.

── Semantics this module fixes ──────────────────────────────────────────────

RANKING is competition-style (RANK(), so 1,1,3 — not 1,2,3). Previously ranks
came from ZREVRANGE position, so 141 students tied on 800 XP received 141
*different* ranks, ordered by the lexicographic accident of their UUID. Tied
students now share a rank, which is both correct and fair.

ORDERING is a deterministic total order (score DESC, id) even where ranks tie.
Pagination requires this: without a unique tiebreaker, rows can repeat or
vanish across pages. The id tiebreak is arbitrary but stable — it decides only
display order *within* a tied rank, never the rank itself.

ELIGIBILITY is score > 0. 5,071 of 5,446 students hold zero XP, so an
unfiltered board is 93% padding. A student with no XP is not ranked; the
envelope reports `total` so the UI can say "375 students on the board" and
prompt them to earn their first XP.

VIEWER RANK is returned regardless of position — the fix for the fact that
the top-100 cutoff (800 XP) made the board meaningless to 97.2% of students.
It is a COUNT of students strictly above the viewer, +1, which is the same
competition-rank definition used for the page itself.

── Phasing ──────────────────────────────────────────────────────────────────

Phase 1 (this) implements Scope.GLOBAL and Window.ALL. The signature already
carries scope/scope_id/window so later phases add a branch, not a rewrite:

  * Phase 2 — Scope.COLLEGE: population filter only (rank by users.xp_total).
  * Phase 3 — Scope.COURSE / BATCH: filters the population AND redefines the
    score, since global xp_total would rank a student on a Linux board for XP
    earned in Python. Course XP must come from user_tutorials joined to
    tutorials (the ledger reconciled in 2026-08), NOT from xp_events — legacy
    event history is incomplete for the imported cohort.
  * Phase 4 — Window.WEEKLY / MONTHLY: sums xp_events over a date range, and
    MUST exclude source_type='reconciliation'. Those 210 back-pay events carry
    a 2026-08-03 timestamp for XP earned months earlier; a naive weekly window
    would rank 210 students by 51,055 XP they did not earn that week.
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User

MAX_LIMIT = 100
DEFAULT_LIMIT = 100


class Scope(str, Enum):
    GLOBAL = "global"


class Window(str, Enum):
    ALL = "all"


def _population(scope: Scope, scope_id: str | None):
    """The WHERE clause defining who is eligible for this board.

    Note `is_test_account.isnot(True)` rather than `!= True`: SQLAlchemy renders
    `!= True` as SQL `!= true`, and `NULL != true` is NULL, which silently drops
    every NULL row. That is exactly how 2,441 real students disappeared from the
    board (migration a1b2c3d4e5f6 made the column NOT NULL, but the NULL-safe
    form is kept here so this query is correct on its own terms).
    """
    filters = [
        User.role == "student",
        User.is_test_account.isnot(True),
        User.xp_total > 0,
    ]
    if scope is Scope.GLOBAL:
        return filters
    raise ValueError(f"unsupported scope: {scope}")


def _entry(user: User, rank: int, viewer_id: str | None) -> dict:
    return {
        "id": str(user.id),
        "rank": rank,
        "xp": user.xp_total,
        "name": user.display_name or "",
        "username": user.username or "",
        "level": user.level,
        "levelTitle": user._level_title(),
        "isCurrentUser": viewer_id is not None and str(user.id) == viewer_id,
    }


async def get_leaderboard(
    db: AsyncSession,
    *,
    scope: Scope = Scope.GLOBAL,
    scope_id: str | None = None,
    window: Window = Window.ALL,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    viewer_id: str | None = None,
) -> dict:
    """Return one page of a leaderboard plus the viewer's own standing."""
    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)
    filters = _population(scope, scope_id)

    # RANK() is evaluated over the whole filtered set before LIMIT/OFFSET slices
    # it, so ranks stay correct (and ties stay shared) on every page.
    rank_col = func.rank().over(order_by=User.xp_total.desc()).label("rank")
    rows = (await db.execute(
        select(User, rank_col)
        .filter(*filters)
        .order_by(User.xp_total.desc(), User.id)
        .limit(limit)
        .offset(offset)
    )).all()

    total = await db.scalar(select(func.count()).select_from(User).filter(*filters)) or 0

    your_rank, your_entry = None, None
    if viewer_id:
        viewer = (await db.execute(
            select(User).filter(User.id == viewer_id, *filters)
        )).scalars().first()
        if viewer is not None:
            ahead = await db.scalar(
                select(func.count()).select_from(User)
                .filter(*filters, User.xp_total > viewer.xp_total)
            ) or 0
            your_rank = ahead + 1
            your_entry = _entry(viewer, your_rank, viewer_id)

    return {
        "scope": {"type": scope.value, "id": scope_id},
        "window": window.value,
        "entries": [_entry(u, r, viewer_id) for u, r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "yourRank": your_rank,
        "yourEntry": your_entry,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
