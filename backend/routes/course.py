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
from dependencies import get_current_user

router = APIRouter(prefix="/api/courses", tags=["courses"])

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
