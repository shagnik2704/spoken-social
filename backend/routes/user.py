from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from dependencies import get_current_user
from models import User, UserCourse, UserTutorial, UserBadge, Tutorial
from models.xp_event import XPEvent
from services.courses import list_admin_courses, list_college_courses



router = APIRouter(prefix='/api', tags=['users'])


@router.get('/me')
async def get_current_user_profile(
    programme_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Returns the logged-in user's full profile + courses + badges."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.courses).selectinload(UserCourse.course),
                 selectinload(User.courses).selectinload(UserCourse.batch),
                 selectinload(User.badges).selectinload(UserBadge.badge))
        .where(User.id == user.id)
    )
    user_loaded = result.scalars().first()
    if not user_loaded:
        raise HTTPException(status_code=404, detail="User not found")

    # Preserve impersonation context from get_current_user dependency
    user_loaded.effective_role = getattr(user, "effective_role", user.role)
    user_loaded.real_user_id = getattr(user, "real_user_id", user.id)
    user_loaded.is_impersonating = getattr(user, "is_impersonating", False)
    user_loaded.target_college_id = getattr(user, "target_college_id", None)
    if user_loaded.target_college_id:
        user_loaded.college_id = user_loaded.target_college_id

    if user_loaded.effective_role == "admin":
        courses = await list_admin_courses(db, programme_id)
    elif user_loaded.effective_role == "coordinator":
        courses = await list_college_courses(db, user_loaded.college_id, programme_id)
    else:
        if programme_id:
            courses = [
                uc.to_api_dict() for uc in user_loaded.courses 
                if uc.batch and uc.batch.programme_id == programme_id
            ]
        else:
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


# NOTE: GET /users/{user_id} was removed. It was unauthenticated and returned
# to_api_dict(), which includes the user's email — so any caller holding a UUID could
# read PII. Nothing in the frontend, tests, scripts or mcp_server called it. Use /me for
# the caller's own profile; anything cross-user belongs behind an admin dependency.


# ===== REQUEST MODELS =====

class TutorialUpdate(BaseModel):
    field: str
    value: Optional[bool] = None

# ===== TUTORIAL ENDPOINTS (protected) =====

@router.get('/me/courses/{course_id}/tutorials')
async def get_my_tutorials(
    course_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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


@router.get('/me/courses/{course_id}/forum-activity')
async def get_my_forum_activity(course_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Returns verified forum activity grouped by tutorial_id.
    Used by the ActiveCourseTracker to show verified forum posts.
    """
    from models.forum_activity import ForumActivity
    from services.forum import activity_to_dict

    # Single query joined on the course (was one query per tutorial), grouped in Python.
    stmt = (
        select(ForumActivity)
        .join(Tutorial, ForumActivity.tutorial_id == Tutorial.id)
        .filter(
            ForumActivity.user_id == user.id,
            Tutorial.course_id == course_id,
            ForumActivity.deleted_on_forum == False,
        )
        .order_by(ForumActivity.posted_at.desc())
    )
    result = await db.execute(stmt)

    activity_by_tutorial: dict[str, list] = {}
    for a in result.scalars().all():
        activity_by_tutorial.setdefault(str(a.tutorial_id), []).append(activity_to_dict(a))

    return activity_by_tutorial


@router.put('/me/courses/{course_id}/tutorials/{tutorial_id}')
async def update_tutorial(
    course_id: str, 
    tutorial_id: str, 
    body: TutorialUpdate,
    batch_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Check if batch is active
    from dependencies import check_batch_active
    await check_batch_active(batch_id, db)

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

    # The path's course_id is what the XPEvent below is tagged with, and course-scoped
    # leaderboards filter on that tag — so a mismatched pair would silently misattribute XP.
    if ut.tutorial.course_id != course_id:
        raise HTTPException(status_code=400, detail="Tutorial does not belong to this course")

    # Map frontend field names → database column names
    field_map = {
        "watched": "watched",
        "practiced": "practiced",
        "assignmentDone": "assignment_done",
        "forumAsked": "forum_asked",
        "forumAnswered": "forum_answered",
        "minitaskOpted": "minitask_opted",
    }

    if body.field not in field_map:
        raise HTTPException(status_code=400, detail="Invalid field")

    # Update the field on the ORM object
    setattr(ut, field_map[body.field], body.value)

    # Auto-complete if practiced
    if body.field == "practiced" and body.value is True:
        ut.status = "completed"

    # Recompute xp_earned from the flags (single source of truth — see services/xp.py).
    from services.xp import recompute_tutorial_xp, recalc_level
    xp_gained = recompute_tutorial_xp(ut)

    # Update user's total XP with the difference and log XP event
    if xp_gained != 0:
        user.xp_total += xp_gained

        # Log XP event (tagged with the course so the daily-XP chart can be course-scoped)
        xp_event = XPEvent(
            user_id=user.id,
            source_type="tutorial_completion" if xp_gained > 0 else "tutorial_reversion",
            source_id=str(tut_uuid),
            xp_delta=xp_gained,
            course_id=course_id,
        )
        db.add(xp_event)

        recalc_level(user)

    await db.commit()

    return ut.to_api_dict()


# NOTE: POST /me/xp was removed. It credited a caller-chosen amount of XP directly and
# was unused by the app (students earn XP via update_tutorial and the forum worker), so it
# was pure attack surface. XP is only ever granted through those verified paths now.
