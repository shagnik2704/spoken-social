from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
from services.jwt import decode_token
import uuid

router = APIRouter(prefix='/api', tags=['leaderboard'])


@router.get('/leaderboard')
def get_leaderboard(request: Request, db: Session = Depends(get_db)):
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

    users = (
        db.query(User)
        .order_by(User.xp_total.desc())
        .limit(100)
        .all()
    )

    result = []
    for rank, user in enumerate(users, start=1):
        result.append({
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

    return result