from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from database import get_db
from dependencies import get_current_user
from models import User, UserCourse, UserTutorial, UserBadge, Tutorial
from models.xp_event import XPEvent
from leaderboard_cache import update_user_xp



router = APIRouter(prefix='/api', tags=['users'])


@router.get('/me')
async def get_current_user_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Returns the logged-in user's full profile + courses + badges."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.courses).selectinload(UserCourse.course),
                 selectinload(User.badges).selectinload(UserBadge.badge))
        .where(User.id == user.id)
    )
    user_loaded = result.scalars().first()
    if not user_loaded:
        raise HTTPException(status_code=404, detail="User not found")

    courses = [uc.to_api_dict() for uc in user_loaded.courses]
    badges = [ub.to_api_dict() for ub in user_loaded.badges]

    return {
        "user": await user_loaded.to_api_dict(db=db),
        "courses": courses,
        "badges": badges,
    }


class ProfileUpdate(BaseModel):
    displayName: Optional[str] = None
    bio: Optional[str] = None
    departmentYear: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None


@router.put('/me')
async def update_current_user_profile(body: ProfileUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Update the logged-in user's editable profile fields."""
    # Map camelCase frontend keys → snake_case DB columns, with max lengths
    field_map = {
        "displayName": ("display_name", 100),
        "bio": ("bio", 500),
        "departmentYear": ("department_year", 128),
        "location": ("location", 100),
        "website": ("website", 255),
    }

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    for frontend_key, value in updates.items():
        col_name, max_len = field_map[frontend_key]
        if value is not None and len(value) > max_len:
            raise HTTPException(status_code=400, detail=f"{frontend_key} must be at most {max_len} characters")
        setattr(user, col_name, value)

    await db.commit()
    await db.refresh(user)

    return {"user": await user.to_api_dict(db=db)}


# ===== PUBLIC: no auth needed =====

@router.get('/users/{user_id}')
async def get_user_by_id(user_id: str, db: AsyncSession = Depends(get_db)):
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await db.execute(
        select(User)
        .options(selectinload(User.courses).selectinload(UserCourse.course),
                 selectinload(User.badges).selectinload(UserBadge.badge))
        .filter_by(id=uid)
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    courses = [uc.to_api_dict() for uc in user.courses]
    badges = [ub.to_api_dict() for ub in user.badges]

    return {
        "user": await user.to_api_dict(db=db),
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
async def get_my_tutorials(course_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(UserTutorial)
        .options(selectinload(UserTutorial.tutorial))
        .join(Tutorial, UserTutorial.tutorial_id == Tutorial.id)
        .filter(UserTutorial.user_id == user.id, Tutorial.course_id == course_id)
        .order_by(Tutorial.tutorial_number)
    )
    result = await db.execute(stmt)
    tutorials = result.scalars().all()
    
    if not tutorials:
        raise HTTPException(status_code=404, detail="No tutorial data found")
    return [t.to_api_dict() for t in tutorials]


@router.put('/me/courses/{course_id}/tutorials/{tutorial_id}')
async def update_tutorial(course_id: str, tutorial_id: str, body: TutorialUpdate,
                    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import uuid
    try:
        tut_uuid = uuid.UUID(tutorial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tutorial ID")

    result = await db.execute(
        select(UserTutorial)
        .options(selectinload(UserTutorial.tutorial))
        .filter_by(user_id=user.id, tutorial_id=tut_uuid)
    )
    ut = result.scalars().first()
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
    XP_MAP = {"watched": 10, "practiced": 10, "assignment_done": 5}
    old_xp = ut.xp_earned
    ut.xp_earned = sum(
        XP_MAP[col] for col in XP_MAP
        if getattr(ut, col) is True
    )

    # Update user's total XP with the difference and log XP event
    xp_gained = ut.xp_earned - old_xp
    if xp_gained != 0:
        user.xp_total += xp_gained

        # Log XP event
        xp_event = XPEvent(
            user_id=user.id,
            source_type="tutorial_completion" if xp_gained > 0 else "tutorial_reversion",
            source_id=str(tut_uuid),
            xp_delta=xp_gained,
        )
        db.add(xp_event)

        # Level up/down check
        xp = user.xp_total
        if xp >= 12000:   user.level = 26
        elif xp >= 7000:  user.level = 21
        elif xp >= 3500:  user.level = 16
        elif xp >= 1500:  user.level = 11
        elif xp >= 500:   user.level = 6
        else:             user.level = 1

    await db.commit()

    if xp_gained!=0:
        await update_user_xp(str(user.id),user.xp_total,{
            "name": user.display_name or "",
            "username": user.username or "",
            "level": user.level,
            "levelTitle": user._level_title(),
            "xpLastWeek": user.xp_last_week,
        })



    return ut.to_api_dict()


# ===== XP ENDPOINT (protected) =====

@router.post('/me/xp')
async def add_xp(body: XPUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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

    await db.commit()
    
    await update_user_xp(str(user.id), user.xp_total, {
        "name": user.display_name or "",
        "username": user.username or "",
        "level": user.level,
        "levelTitle": user._level_title(),
        "xpLastWeek": user.xp_last_week,
    })




    return {"xpTotal": user.xp_total, "level": user.level, "levelTitle": user._level_title()}
