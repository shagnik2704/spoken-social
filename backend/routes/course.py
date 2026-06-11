# ============================================================
# Course & Batch routes — listing and management
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from database import get_db
from models import Course, Batch, CollegeCourse, User
from models.course import UserCourse
from dependencies import get_current_user

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/me")
async def get_my_courses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get courses relevant to the current user (enrolled for student, college-enabled for coordinator, all for admin)."""
    if user.effective_role == "admin":
        result = await db.execute(
            select(Course)
            .options(selectinload(Course.batches))
            .order_by(Course.title)
        )
        all_courses = result.scalars().all()
        data = []
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
            data.append(c_dict)
        return data

    elif user.effective_role == "coordinator":
        result = await db.execute(
            select(Course)
            .join(CollegeCourse, CollegeCourse.course_id == Course.id)
            .filter(CollegeCourse.college_id == user.college_id)
            .options(selectinload(Course.batches))
            .order_by(Course.title)
        )
        col_courses = result.scalars().all()
        data = []
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
            data.append(c_dict)
        return data

    else:
        result = await db.execute(
            select(UserCourse)
            .options(
                selectinload(UserCourse.course),
                selectinload(UserCourse.batch),
            )
            .filter(UserCourse.user_id == user.id)
        )
        enrollments = result.scalars().all()
        return [uc.to_api_dict() for uc in enrollments]

@router.get("/all-with-batches")
async def list_courses_with_batches(
    db: AsyncSession = Depends(get_db)
):
    """List all courses with their associated batches for landing page selection."""
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.batches))
        .order_by(Course.title)
    )
    courses = result.scalars().all()
    
    data = []
    for c in courses:
        c_dict = c.to_api_dict() if hasattr(c, 'to_api_dict') else {"id": c.id, "title": c.title, "description": c.description}
        c_dict["batches"] = [b.to_api_dict() for b in c.batches]
        data.append(c_dict)
    
    return data


@router.get("")
async def list_courses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all courses. 
    Admin sees all. 
    Coordinators/Students see courses enabled for their college.
    """
    if user.effective_role == "admin":
        result = await db.execute(select(Course).order_by(Course.title))
        courses = result.scalars().all()
    else:
        # Filter by college enrollment
        result = await db.execute(
            select(Course)
            .join(CollegeCourse, CollegeCourse.course_id == Course.id)
            .filter(CollegeCourse.college_id == user.college_id)
            .order_by(Course.title)
        )
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
