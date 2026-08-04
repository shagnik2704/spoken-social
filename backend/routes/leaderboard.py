from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from database import get_db
from models import User
from models.xp_event import XPEvent
from services.jwt import decode_token
from services.leaderboard import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Scope,
    UnknownScopeTarget,
    Window,
    WINDOW_EXCLUDED_SOURCES,
    get_leaderboard as build_leaderboard,
)
from dependencies import get_current_user
import uuid
import calendar
from datetime import date, datetime

router = APIRouter(prefix='/api', tags=['leaderboard'])


def _viewer_id(request: Request) -> str | None:
    """The caller's id, or None. The board is public, so a missing or bad token
    is not an error.

    'eff' before 'sub' matches dependencies.get_current_user, so an admin
    impersonating a student sees the student highlighted.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    payload = decode_token(auth_header[7:])
    if not payload:
        return None
    try:
        return str(uuid.UUID(str(payload.get("eff") or payload.get("sub"))))
    except (ValueError, TypeError, AttributeError):
        return None


@router.get('/leaderboard')
async def get_leaderboard(
    request: Request,
    scope: Scope = Query(Scope.GLOBAL, description="Which board to return"),
    scope_id: str | None = Query(None, description="Target of the scope, e.g. a college id"),
    window: Window = Query(Window.ALL, description="Time window the scores cover"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """One page of a leaderboard, plus the caller's own standing."""
    try:
        return await build_leaderboard(
            db,
            scope=scope,
            scope_id=scope_id,
            window=window,
            limit=limit,
            offset=offset,
            viewer_id=_viewer_id(request),
        )
    except UnknownScopeTarget as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get('/xp-history')
async def get_xp_history(
    current_user: User = Depends(get_current_user),
    month: str = Query(None, description="Month in YYYY-MM format, defaults to current month"),
    db: AsyncSession = Depends(get_db),
):
    """Returns daily XP gained for the authenticated user in a given month."""

    # Parse month param or default to current month
    today = date.today()
    if month:
        try:
            year, mon = month.split('-')
            year, mon = int(year), int(mon)
        except (ValueError, AttributeError):
            year, mon = today.year, today.month
    else:
        year, mon = today.year, today.month

    # Get number of days in the month
    _, num_days = calendar.monthrange(year, mon)

    # Build date range
    start_date = datetime(year, mon, 1)
    if mon == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, mon + 1, 1)

    # Query: aggregate xp_delta by day, bucketing in IST (created_at is timestamptz; the
    # audience is IST, so days must run midnight-to-midnight local, not UTC). Both the day
    # extraction AND the month boundaries use the same IST wall-clock for consistency.
    from config import APP_TIMEZONE
    ist_ts = func.timezone(APP_TIMEZONE, XPEvent.created_at)  # IST wall-clock (naive ts)
    result = await db.execute(
        select(
            func.extract('day', ist_ts).label('day'),
            func.coalesce(func.sum(XPEvent.xp_delta), 0).label('xp'),
        )
        .filter(
            XPEvent.user_id == current_user.id,
            ist_ts >= start_date,
            ist_ts < end_date,
            # Same exclusion the windowed leaderboard applies: reconciliation rows carry the
            # back-pay run's timestamp, not the date of the work, so they would land as one
            # artificial spike on the day the script ran.
            XPEvent.source_type.notin_(WINDOW_EXCLUDED_SOURCES),
        )
        .group_by(func.extract('day', ist_ts))
    )
    rows = result.all()

    # Build a lookup dict: day -> xp
    day_xp = {int(row.day): int(row.xp) for row in rows}

    # Fill all days
    days = [{"day": d, "xp": day_xp.get(d, 0)} for d in range(1, num_days + 1)]

    return {"month": f"{year:04d}-{mon:02d}", "days": days}