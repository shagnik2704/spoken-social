from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from database import get_db
from dependencies import get_current_user
from models import User, UserCourse, UserTutorial, UserBadge, Tutorial, Course, CollegeCourse
from models.xp_event import XPEvent
from leaderboard_cache import update_user_xp
from services.forum import get_forum_activity_for_tutorial



router = APIRouter(prefix='/api', tags=['users'])


@router.get('/me')
async def get_current_user_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
    print(f"DEBUG /ME: user={user_loaded.email}, effective_role={user_loaded.effective_role}, target_college_id={user_loaded.target_college_id}")
    if user_loaded.target_college_id:
        user_loaded.college_id = user_loaded.target_college_id

    if user_loaded.effective_role == "admin":
        # Fetch all courses with their batches
        courses_res = await db.execute(
            select(Course)
            .options(selectinload(Course.batches))
            .order_by(Course.title)
        )
        all_courses = courses_res.scalars().all()
        courses = []
        for c in all_courses:
            c_dict = c.to_api_dict() if hasattr(c, 'to_api_dict') else {"id": c.id, "title": c.title, "description": c.description}
            c_dict["batches"] = [b.to_api_dict() for b in c.batches]
            active_b = next((b for b in c.batches if b.status == "active"), c.batches[0] if c.batches else None)
            if active_b:
                c_dict["batchId"] = str(active_b.id)
                c_dict["batchName"] = active_b.name
                c_dict["batchStatus"] = active_b.computed_status
            else:
                c_dict["batchId"] = None
                c_dict["batchName"] = None
                c_dict["batchStatus"] = "inactive"
            courses.append(c_dict)
    elif user_loaded.effective_role == "coordinator":
        # Fetch courses enabled for coordinator's college, with batches
        courses_res = await db.execute(
            select(Course)
            .join(CollegeCourse, CollegeCourse.course_id == Course.id)
            .filter(CollegeCourse.college_id == user_loaded.college_id)
            .options(selectinload(Course.batches))
            .order_by(Course.title)
        )
        col_courses = courses_res.scalars().all()
        courses = []
        for c in col_courses:
            c_dict = c.to_api_dict() if hasattr(c, 'to_api_dict') else {"id": c.id, "title": c.title, "description": c.description}
            c_dict["batches"] = [b.to_api_dict() for b in c.batches]
            active_b = next((b for b in c.batches if b.status == "active"), c.batches[0] if c.batches else None)
            if active_b:
                c_dict["batchId"] = str(active_b.id)
                c_dict["batchName"] = active_b.name
                c_dict["batchStatus"] = active_b.computed_status
            else:
                c_dict["batchId"] = None
                c_dict["batchName"] = None
                c_dict["batchStatus"] = "inactive"
            courses.append(c_dict)
    else:
        courses = [uc.to_api_dict() for uc in user_loaded.courses]

    badges = [ub.to_api_dict() for ub in user_loaded.badges]

    print(f"DEBUG /ME: user_loaded={user_loaded.email}, final_role={user_loaded.effective_role}, college_id={user_loaded.college_id}")
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
                 selectinload(User.courses).selectinload(UserCourse.batch),
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
    batch_id: Optional[str] = None


# ===== TUTORIAL ENDPOINTS (protected) =====

@router.get('/me/courses/{course_id}/tutorials')
async def get_my_tutorials(
    course_id: str, 
    batch_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(UserTutorial)
        .options(selectinload(UserTutorial.tutorial))
        .join(Tutorial, UserTutorial.tutorial_id == Tutorial.id)
        .filter(UserTutorial.user_id == user.id, Tutorial.course_id == course_id)
    )
    
    if batch_id:
        # Filter tutorials associated with this specific batch enrollment
        pass # In our simplified schema, UserTutorial isn't directly batch-linked yet, 
             # but UserCourse is. For now, we return all for the course.
    
    stmt = stmt.order_by(Tutorial.tutorial_number)
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
    # Get all tutorials for this course
    stmt = (
        select(Tutorial)
        .filter(Tutorial.course_id == course_id)
        .order_by(Tutorial.tutorial_number)
    )
    result = await db.execute(stmt)
    tutorials = result.scalars().all()

    activity_by_tutorial = {}
    for tutorial in tutorials:
        activities = await get_forum_activity_for_tutorial(db, user.id, tutorial.id)
        if activities:
            activity_by_tutorial[str(tutorial.id)] = activities

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

    # Recalculate XP
    XP_MAP = {
        "watched": 10, 
        "practiced": 10, 
        "assignment_done": 5,
        "forum_asked": 5,
        "forum_answered": 10
    }
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
async def add_xp(
    body: XPUpdate, 
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Check if batch is active
    from dependencies import check_batch_active
    await check_batch_active(body.batch_id, db)

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
