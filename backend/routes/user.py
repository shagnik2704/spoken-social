from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from dependencies import get_current_user
from models import User, UserCourse, UserTutorial, UserBadge, Tutorial
from models.xp_event import XPEvent


router = APIRouter(prefix='/api', tags=['users'])


@router.get('/me')
def get_current_user_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the logged-in user's full profile + courses + badges."""
    courses = [uc.to_api_dict() for uc in user.courses]
    badges = [ub.to_api_dict() for ub in user.badges]

    return {
        "user": user.to_api_dict(db=db),
        "courses": courses,
        "badges": badges,
    }


# ===== PUBLIC: no auth needed =====

@router.get('/users/{user_id}')
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = db.query(User).filter_by(id=uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    courses = [uc.to_api_dict() for uc in user.courses]
    badges = [ub.to_api_dict() for ub in user.badges]

    return {
        "user": user.to_api_dict(db=db),
        "courses": courses,
        "badges": badges,
    }


# ===== REQUEST MODELS =====

class TutorialUpdate(BaseModel):
    field: str
    value: Optional[bool] = None

class XPUpdate(BaseModel):
    amount: int
    source: str


# ===== TUTORIAL ENDPOINTS (protected) =====

@router.get('/me/courses/{course_id}/tutorials')
def get_my_tutorials(course_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tutorials = (
        db.query(UserTutorial)
        .join(Tutorial, UserTutorial.tutorial_id == Tutorial.id)
        .filter(UserTutorial.user_id == user.id, Tutorial.course_id == course_id)
        .order_by(Tutorial.tutorial_number)
        .all()
    )
    if not tutorials:
        raise HTTPException(status_code=404, detail="No tutorial data found")
    return [t.to_api_dict() for t in tutorials]


@router.put('/me/courses/{course_id}/tutorials/{tutorial_id}')
def update_tutorial(course_id: str, tutorial_id: str, body: TutorialUpdate,
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import uuid
    try:
        tut_uuid = uuid.UUID(tutorial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tutorial ID")

    ut = db.query(UserTutorial).filter_by(user_id=user.id, tutorial_id=tut_uuid).first()
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
    if body.field == "practiced" and body.value is True:
        ut.status = "completed"

    # Recalculate XP
    XP_MAP = {"watched": 10, "practiced": 10, "assignment_done": 5, "forum_asked": 5, "forum_answered": 5}
    old_xp = ut.xp_earned
    ut.xp_earned = sum(
        XP_MAP[col] for col in XP_MAP
        if getattr(ut, col) is True
    )

    # Update user's total XP with the difference and log XP event
    xp_gained = ut.xp_earned - old_xp
    if xp_gained > 0:
        user.xp_total += xp_gained

        # Log XP event
        xp_event = XPEvent(
            user_id=user.id,
            source_type="tutorial_completion",
            source_id=str(tut_uuid),
            xp_delta=xp_gained,
        )
        db.add(xp_event)

        # Level up check
        xp = user.xp_total
        if xp >= 12000:   user.level = 26
        elif xp >= 7000:  user.level = 21
        elif xp >= 3500:  user.level = 16
        elif xp >= 1500:  user.level = 11
        elif xp >= 500:   user.level = 6
        else:             user.level = 1

    db.commit()
    return ut.to_api_dict()


# ===== XP ENDPOINT (protected) =====

@router.post('/me/xp')
def add_xp(body: XPUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.xp_total += body.amount

    # Log XP event
    xp_event = XPEvent(
        user_id=user.id,
        source_type=body.source,
        source_id="",
        xp_delta=body.amount,
    )
    db.add(xp_event)

    # Level up logic
    xp = user.xp_total
    if xp >= 12000:   user.level = 26
    elif xp >= 7000:  user.level = 21
    elif xp >= 3500:  user.level = 16
    elif xp >= 1500:  user.level = 11
    elif xp >= 500:   user.level = 6
    else:             user.level = 1

    db.commit()
    return {"xpTotal": user.xp_total, "level": user.level, "levelTitle": user._level_title()}
