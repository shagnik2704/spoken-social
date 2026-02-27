
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import User, UserCourse, UserTutorial, UserBadge, Tutorial


router = APIRouter(prefix='/api', tags=['users'])



@router.get('/me')
def get_current_user_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the logged-in user's full profile + courses + badges.
    'user' is a User ORM object resolved from the JWT token.
    """
    # user.courses is a list of UserCourse objects (thanks to relationship())
    courses = [uc.to_api_dict() for uc in user.courses]
    
    # user.badges is a list of UserBadge objects
    badges = [ub.to_api_dict() for ub in user.badges]

    return {
        "user": user.to_api_dict(),
        "weeklyGoal": user.weekly_goal,
        "courses": courses,
        "badges": badges,
    }


# ===== PUBLIC: no auth needed =====

@router.get('/users/{user_id}')
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    courses = [uc.to_api_dict() for uc in user.courses]
    badges = [ub.to_api_dict() for ub in user.badges]

    return {
        "user": user.to_api_dict(),
        "weeklyGoal": user.weekly_goal,
        "courses": courses,
        "badges": badges,
    }


# ===== REQUEST MODELS =====

class TutorialUpdate(BaseModel):
    field: str
    value: Optional[str] = None

class XPUpdate(BaseModel):
    amount: int
    source: str


# ===== TUTORIAL ENDPOINTS (protected) =====

@router.get('/me/courses/{course_id}/tutorials')
def get_my_tutorials(course_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tutorials = (
        db.query(UserTutorial)
        .join(Tutorial, UserTutorial.tutorial_id == Tutorial.id)
        .filter(UserTutorial.user_id == user.id, UserTutorial.course_id == course_id)
        .order_by(Tutorial.number)
        .all()
    )
    if not tutorials:
        raise HTTPException(status_code=404, detail="No tutorial data found")
    return [t.to_api_dict() for t in tutorials]


@router.put('/me/courses/{course_id}/tutorials/{tutorial_id}')
def update_tutorial(course_id: str, tutorial_id: str, body: TutorialUpdate,
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    ut = db.query(UserTutorial).filter_by(user_id=user.id, tutorial_id=tutorial_id, course_id=course_id).first()
    if not ut:
        raise HTTPException(status_code=404, detail="Tutorial not found")

    # Map frontend field names → database column names
    field_map = {
        "watched": "watched",
        "practiced": "practiced",
        "assignmentDone": "assignment_done",
        "forumAsked": "forum_asked",
        "forumAnswered": "forum_answered",
    }

    if body.field not in field_map:
        raise HTTPException(status_code=400, detail="Invalid field")

    # Update the field on the ORM object
    setattr(ut, field_map[body.field], body.value)

    # Auto-complete if practiced
    if body.field == "practiced" and body.value == "yes":
        ut.completed = True

    # Recalculate XP
    XP_MAP = {"watched": 10, "practiced": 10, "assignment_done": 5, "forum_asked": 5, "forum_answered": 5}
    old_xp=ut.xp_earned
    ut.xp_earned = sum(
        XP_MAP[col] for col in XP_MAP
        if getattr(ut, col) == "yes"
    )

    # Update user's total XP with the difference
    xp_gained = ut.xp_earned - old_xp
    if xp_gained > 0:
        user.xp_total += xp_gained
        user.xp_today += xp_gained
        user.xp_this_week += xp_gained

        # Level up check
        xp = user.xp_total
        if xp >= 12000:   user.level, user.level_title = 26, "Spoken Legend"
        elif xp >= 7000:  user.level, user.level_title = 21, "Master"
        elif xp >= 3500:  user.level, user.level_title = 16, "Expert"
        elif xp >= 1500:  user.level, user.level_title = 11, "Practitioner"
        elif xp >= 500:   user.level, user.level_title = 6, "Explorer"
        else:             user.level, user.level_title = 1, "Beginner"

    db.commit()
    return ut.to_api_dict()


# ===== XP ENDPOINT (protected) =====

@router.post('/me/xp')
def add_xp(body: XPUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.xp_total += body.amount
    user.xp_today += body.amount
    user.xp_this_week += body.amount

    # Level up logic
    xp = user.xp_total
    if xp >= 12000:   user.level, user.level_title = 26, "Spoken Legend"
    elif xp >= 7000:  user.level, user.level_title = 21, "Master"
    elif xp >= 3500:  user.level, user.level_title = 16, "Expert"
    elif xp >= 1500:  user.level, user.level_title = 11, "Practitioner"
    elif xp >= 500:   user.level, user.level_title = 6, "Explorer"
    else:             user.level, user.level_title = 1, "Beginner"

    db.commit()  # ← saves XP to PostgreSQL
    return {"xpTotal": user.xp_total, "level": user.level, "levelTitle": user.level_title}
