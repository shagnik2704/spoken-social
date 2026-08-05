# ============================================================
# Course & Batch routes — listing and management
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from database import get_db
from models import Course, Batch, CollegeCourse, User
from models.course import UserCourse
from dependencies import get_current_user
from services.courses import list_admin_courses, list_college_courses

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/me")
async def get_my_courses(
    programme_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get courses relevant to the current user (enrolled for student, college-enabled for coordinator, all for admin)."""
    if user.effective_role == "admin":
        return await list_admin_courses(db, programme_id)

    elif user.effective_role == "coordinator":
        return await list_college_courses(db, user.college_id, programme_id)

    else:
        query = (
            select(UserCourse)
            .options(
                selectinload(UserCourse.course),
                selectinload(UserCourse.batch),
            )
            .filter(UserCourse.user_id == user.id)
        )
        if programme_id:
            query = query.join(Batch, UserCourse.batch_id == Batch.id).filter(Batch.programme_id == programme_id)
        result = await db.execute(query)
        enrollments = result.scalars().all()
        return [uc.to_api_dict() for uc in enrollments]

@router.get("/all-with-batches")
async def list_courses_with_batches(
    programme_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all courses with their associated batches for landing page selection."""
    query = select(Course).options(selectinload(Course.batches))
    if programme_id:
        from models.programme import ProgrammeCourse
        query = query.join(ProgrammeCourse, ProgrammeCourse.course_id == Course.id).filter(ProgrammeCourse.programme_id == programme_id)
    query = query.order_by(Course.title)
    
    result = await db.execute(query)
    courses = result.scalars().all()
    
    data = []
    for c in courses:
        c_dict = c.to_api_dict() if hasattr(c, 'to_api_dict') else {"id": c.id, "title": c.title, "description": c.description}
        batches = [b for b in c.batches if b.programme_id == programme_id] if programme_id else c.batches
        c_dict["batches"] = [b.to_api_dict() for b in batches]
        data.append(c_dict)
    
    return data


@router.get("")
async def list_courses(
    programme_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all courses. 
    Admin sees all. 
    Coordinators/Students see courses enabled for their college.
    """
    if user.effective_role == "admin":
        query = select(Course)
        if programme_id:
            from models.programme import ProgrammeCourse
            query = query.join(ProgrammeCourse, ProgrammeCourse.course_id == Course.id).filter(ProgrammeCourse.programme_id == programme_id)
        query = query.order_by(Course.title)
        result = await db.execute(query)
        courses = result.scalars().all()
    else:
        # Filter by college enrollment
        query = (
            select(Course)
            .join(CollegeCourse, CollegeCourse.course_id == Course.id)
            .filter(CollegeCourse.college_id == user.college_id)
        )
        if programme_id:
            query = query.filter(CollegeCourse.programme_id == programme_id)
        query = query.order_by(Course.title)
        result = await db.execute(query)
        courses = result.scalars().all()
    
    return [c.to_api_dict() if hasattr(c, 'to_api_dict') else {"id": c.id, "title": c.title, "description": c.description} for c in courses]


@router.get("/{course_id}/batches")
async def list_batches(
    course_id: str,
    status: Optional[str] = Query(None), # active | inactive
    db: AsyncSession = Depends(get_db)
):
    """List batches for a specific course."""
    query = select(Batch).options(selectinload(Batch.course)).filter(Batch.course_id == course_id)
    if status:
        query = query.filter(Batch.status == status)
    
    result = await db.execute(query.order_by(Batch.start_date.desc()))
    batches = result.scalars().all()
    
    return [b.to_api_dict() for b in batches]


@router.get("/{course_id}/batches/active")
async def get_active_batch(course_id: str, db: AsyncSession = Depends(get_db)):
    """Get the currently active batch for a course."""
    result = await db.execute(
        select(Batch)
        .filter(Batch.course_id == course_id, Batch.status == "active")
        .order_by(Batch.start_date.desc())
    )
    batch = result.scalars().first()
    if not batch:
        raise HTTPException(status_code=404, detail="No active batch found for this course")
    return batch.to_api_dict()
