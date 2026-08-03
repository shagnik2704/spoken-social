"""Leaderboard queries.

Reads straight from Postgres rather than a cache. The full reasoning is in
docs/leaderboard-cache-coherence.md; in short, every leaderboard bug in the
2026-08 audit was a coherence failure between a hand-synced Redis mirror and
the database, and a top-N over a descending index costs the same at 100,000
students as at 5,000.

Semantics:

  Ranking is competition-style (RANK), so tied students share a rank: 1, 1, 3
  rather than 1, 2, 3. Ordering adds a unique tiebreaker after the score so the
  order is total, which pagination depends on — the tiebreak decides display
  order within a tie, never the rank itself.

  Eligibility is score > 0. Most students have never earned XP, so an
  unfiltered board is mostly padding, and a student with no XP is reported as
  unranked rather than last.

  The viewer's rank is returned whether or not they appear on the requested
  page, since the visible page is a small fraction of the ranked population.

  A scope narrows the population; it does not change what counts as score.
  Course and batch scopes (phase 3) will change both, because ranking a student
  on a Linux board by XP they earned in Python would be wrong.
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
    COLLEGE = "college"


class Window(str, Enum):
    ALL = "all"


SCOPES_REQUIRING_ID = {Scope.COLLEGE}


class UnknownScopeTarget(Exception):
    """The scope is valid but names something that doesn't exist."""


def _population(scope: Scope, scope_id: str | None):
    filters = [
        User.role == "student",
        # isnot(True), not != True: `NULL != true` is NULL in SQL, which
        # silently drops the row.
        User.is_test_account.isnot(True),
        User.xp_total > 0,
    ]
    if scope is Scope.COLLEGE:
        filters.append(User.college_id == scope_id)
    return filters


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


async def _scope_label(db: AsyncSession, scope: Scope, scope_id: str | None) -> str | None:
    if scope is not Scope.COLLEGE:
        return None
    from models.college import College

    name = await db.scalar(select(College.name).filter(College.id == scope_id))
    if name is None:
        raise UnknownScopeTarget(f"no college with id {scope_id!r}")
    return name


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
    """One page of a leaderboard, plus the viewer's own standing.

    The viewer's rank is returned whether or not they appear on the page.
    """
    scope, window = Scope(scope), Window(window)
    if scope in SCOPES_REQUIRING_ID and not scope_id:
        raise ValueError(f"scope '{scope.value}' requires a scope_id")

    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)
    filters = _population(scope, scope_id)
    label = await _scope_label(db, scope, scope_id)

    # RANK() is evaluated over the whole filtered set before LIMIT slices it, so
    # ranks stay absolute and ties stay shared across pages. The trailing id in
    # ORDER BY makes the order total, which pagination needs.
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
        "scope": {"type": scope.value, "id": scope_id, "name": label},
        "window": window.value,
        "entries": [_entry(u, r, viewer_id) for u, r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "yourRank": your_rank,
        "yourEntry": your_entry,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
