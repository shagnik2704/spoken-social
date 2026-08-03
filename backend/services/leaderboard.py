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

  A scope changes who is on the board, and may also change what counts as
  score. Global and college boards rank on total XP: a college narrows the
  population but a student's score is the same one they see everywhere. A
  course board instead ranks on XP earned in that course, because carrying
  global XP over would let a student top a course they have barely touched on
  the strength of work done elsewhere.

  All-time course scores are summed from user_tutorials, not from xp_events.
  The event history is incomplete for the cohort imported in early 2026, while
  the tutorial rows were reconciled against their flags and are exact.

  A window restricts the score to XP earned since the start of the current
  calendar week (Monday) or month, computed in APP_TIMEZONE because the
  audience is Indian and a "week" should reset at midnight IST, not UTC.
  Window scores sum xp_events over the period — the journal is complete for
  anything recent — and exclude reconciliation events: those carry the
  timestamp of the 2026-08 back-pay run, not of the months-old work they
  settle, so a naive weekly board would rank 210 students by 51k XP they did
  not earn that week. Course windows additionally filter events by course_id,
  which every event written since the course_id column landed carries.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import APP_TIMEZONE
from models.tutorial import Tutorial, UserTutorial
from models.user import User
from models.xp_event import XPEvent

MAX_LIMIT = 100
DEFAULT_LIMIT = 100

WINDOW_EXCLUDED_SOURCES = ("reconciliation",)


class Scope(str, Enum):
    GLOBAL = "global"
    COLLEGE = "college"
    COURSE = "course"


class Window(str, Enum):
    ALL = "all"
    MONTHLY = "monthly"
    WEEKLY = "weekly"


SCOPES_REQUIRING_ID = {Scope.COLLEGE, Scope.COURSE}


class UnknownScopeTarget(Exception):
    """The scope is valid but names something that doesn't exist."""


def window_start(window: Window, now: datetime | None = None) -> datetime | None:
    """Start of the current calendar window in APP_TIMEZONE, or None for all time."""
    if window is Window.ALL:
        return None
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(APP_TIMEZONE))
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if window is Window.MONTHLY:
        return midnight.replace(day=1)
    return midnight - timedelta(days=local.weekday())


def _course_xp(course_id: str):
    """Per-student all-time XP earned within one course."""
    return (
        select(
            UserTutorial.user_id.label("user_id"),
            func.coalesce(func.sum(UserTutorial.xp_earned), 0).label("xp"),
        )
        .join(Tutorial, Tutorial.id == UserTutorial.tutorial_id)
        .filter(Tutorial.course_id == course_id)
        .group_by(UserTutorial.user_id)
        .subquery()
    )


def _window_xp(start: datetime, course_id: str | None):
    """Per-student XP earned since `start`, from the event journal."""
    stmt = (
        select(
            XPEvent.user_id.label("user_id"),
            func.coalesce(func.sum(XPEvent.xp_delta), 0).label("xp"),
        )
        .filter(
            XPEvent.created_at >= start,
            # NULL-safe: `source_type NOT IN (...)` is NULL for NULL source_type
            # and would silently drop the row — the `!= True` trap again.
            or_(
                XPEvent.source_type.is_(None),
                XPEvent.source_type.notin_(WINDOW_EXCLUDED_SOURCES),
            ),
        )
        .group_by(XPEvent.user_id)
    )
    if course_id is not None:
        stmt = stmt.filter(XPEvent.course_id == course_id)
    return stmt.subquery()


def _board(scope: Scope, scope_id: str | None, start: datetime | None):
    """The score column, the table it comes from, and the population filters."""
    filters = [User.role == "student", User.is_test_account.isnot(True)]

    if start is not None:
        source = _window_xp(start, scope_id if scope is Scope.COURSE else None)
        if scope is Scope.COLLEGE:
            filters.append(User.college_id == scope_id)
        return source.c.xp, source, [*filters, source.c.xp > 0]

    if scope is Scope.COURSE:
        source = _course_xp(scope_id)
        return source.c.xp, source, [*filters, source.c.xp > 0]

    if scope is Scope.COLLEGE:
        filters.append(User.college_id == scope_id)
    return User.xp_total, None, [*filters, User.xp_total > 0]


def _join(stmt, source):
    return stmt if source is None else stmt.join(source, source.c.user_id == User.id)


def _entry(user: User, rank: int, score: int, viewer_id: str | None) -> dict:
    return {
        "id": str(user.id),
        "rank": rank,
        "xp": score,
        "name": user.display_name or "",
        "username": user.username or "",
        "level": user.level,
        "levelTitle": user._level_title(),
        "isCurrentUser": viewer_id is not None and str(user.id) == viewer_id,
    }


async def _scope_label(db: AsyncSession, scope: Scope, scope_id: str | None) -> str | None:
    if scope is Scope.COLLEGE:
        from models.college import College

        name = await db.scalar(select(College.name).filter(College.id == scope_id))
        if name is None:
            raise UnknownScopeTarget(f"no college with id {scope_id!r}")
        return name

    if scope is Scope.COURSE:
        from models.course import Course

        title = await db.scalar(select(Course.title).filter(Course.id == scope_id))
        if title is None:
            raise UnknownScopeTarget(f"no course with id {scope_id!r}")
        return title

    return None


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
    label = await _scope_label(db, scope, scope_id)
    start = window_start(window)
    score, source, filters = _board(scope, scope_id, start)

    # RANK() is evaluated over the whole filtered set before LIMIT slices it, so
    # ranks stay absolute and ties stay shared across pages.
    rank_col = func.rank().over(order_by=score.desc()).label("rank")
    rows = (await db.execute(
        _join(select(User, score.label("score"), rank_col), source)
        .filter(*filters)
        .order_by(score.desc(), User.id)
        .limit(limit)
        .offset(offset)
    )).all()

    total = await db.scalar(
        _join(select(func.count()).select_from(User), source).filter(*filters)
    ) or 0

    your_rank, your_entry = None, None
    if viewer_id:
        viewer = (await db.execute(
            _join(select(User, score.label("score")), source)
            .filter(User.id == viewer_id, *filters)
        )).first()
        if viewer is not None:
            user, viewer_score = viewer
            ahead = await db.scalar(
                _join(select(func.count()).select_from(User), source)
                .filter(*filters, score > viewer_score)
            ) or 0
            your_rank = ahead + 1
            your_entry = _entry(user, your_rank, viewer_score, viewer_id)

    return {
        "scope": {"type": scope.value, "id": scope_id, "name": label},
        "window": window.value,
        "windowStart": start.isoformat() if start else None,
        "entries": [_entry(u, r, s, viewer_id) for u, s, r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "yourRank": your_rank,
        "yourEntry": your_entry,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
