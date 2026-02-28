from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

router = APIRouter(prefix='/api', tags=['leaderboard'])


@router.get('/leaderboard')
def get_leaderboard(db: Session = Depends(get_db)):
    """Returns all-time leaderboard — top users by xp_total."""
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
            "isCurrentUser": False,
        })

    return result