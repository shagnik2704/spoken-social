from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from database import get_db
from models import User
from models.xp_event import XPEvent
from services.jwt import decode_token
from dependencies import get_current_user
import uuid
import calendar
from datetime import date, datetime

router = APIRouter(prefix='/api', tags=['leaderboard'])


@router.get('/leaderboard')
async def get_leaderboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Returns all-time leaderboard — top users by xp_total."""

    # Try to identify the current user from the Authorization header (optional)
    current_user_id = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user_id_str = decode_token(token)
        if user_id_str:
            try:
                current_user_id = uuid.UUID(user_id_str)
            except ValueError:
                pass

    result = await db.execute(
        select(User)
        .order_by(User.xp_total.desc())
        .limit(100)
    )
    users = result.scalars().all()

    leaderboard = []
    for rank, user in enumerate(users, start=1):
        leaderboard.append({
            "id": str(user.id),
            "rank": rank,
            "name": user.display_name,
            "username": user.username,
            "level": user.level,
            "levelTitle": user._level_title(),
            "xp": user.xp_total,
            "xpLastWeek": user.xp_last_week,
            "trend": "same",
            "trendDelta": 0,
            "isCurrentUser": current_user_id is not None and user.id == current_user_id,
        })

    return leaderboard


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

    # Query: aggregate xp_delta by day
    result = await db.execute(
        select(
            func.extract('day', XPEvent.created_at).label('day'),
            func.coalesce(func.sum(XPEvent.xp_delta), 0).label('xp'),
        )
        .filter(
            XPEvent.user_id == current_user.id,
            XPEvent.created_at >= start_date,
            XPEvent.created_at < end_date,
        )
        .group_by(func.extract('day', XPEvent.created_at))
    )
    rows = result.all()

    # Build a lookup dict: day -> xp
    day_xp = {int(row.day): int(row.xp) for row in rows}

    # Fill all days
    days = [{"day": d, "xp": day_xp.get(d, 0)} for d in range(1, num_days + 1)]

    return {"month": f"{year:04d}-{mon:02d}", "days": days}