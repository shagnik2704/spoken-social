# ============================================================
# Programme routes — programme listing & filtering
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload
from typing import Optional

from database import get_db
from models import User, Course, Batch, CollegeCourse, UserCourse
from models.programme import Programme, ProgrammeCourse
from dependencies import get_current_user

router = APIRouter(prefix="/api/programmes", tags=["programmes"])


@router.get("")
async def list_programmes(db: AsyncSession = Depends(get_db)):
    """List all active programmes (public, for the selector)."""
    result = await db.execute(
        select(Programme)
        .filter(Programme.is_active == True)
        .order_by(Programme.display_order)
    )
    programmes = result.scalars().all()

    data = []
    for p in programmes:
        # Count courses in this programme
        course_count_res = await db.execute(
            select(func.count()).select_from(ProgrammeCourse).filter(ProgrammeCourse.programme_id == p.id)
        )
        course_count = course_count_res.scalar() or 0

        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "icon": p.icon,
            "color": p.color,
            "isActive": p.is_active,
            "displayOrder": p.display_order,
            "courseCount": course_count,
        })
    return data


@router.get("/me")
async def get_my_programmes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List programmes accessible to the current user.
    - Admin: all active programmes
    - Coordinator: programmes where their college has at least one course enrolled
    - Student: programmes where they have an enrollment (via batch.programme_id)
    """
    if user.effective_role == "admin":
        # Admin sees all
        result = await db.execute(
            select(Programme)
            .filter(Programme.is_active == True)
            .order_by(Programme.display_order)
        )
        programmes = result.scalars().all()

    elif user.effective_role == "coordinator":
        # Coordinator sees programmes where their college has course enrollments
        result = await db.execute(
            select(Programme)
            .join(ProgrammeCourse, ProgrammeCourse.programme_id == Programme.id)
            .join(CollegeCourse, (
                (CollegeCourse.course_id == ProgrammeCourse.course_id) &
                (CollegeCourse.programme_id == Programme.id)
            ))
            .filter(
                CollegeCourse.college_id == user.college_id,
                Programme.is_active == True,
            )
            .distinct()
            .order_by(Programme.display_order)
        )
        programmes = result.scalars().all()

    else:
        # Student sees programmes where they have enrollments
        result = await db.execute(
            select(Programme)
            .join(Batch, Batch.programme_id == Programme.id)
            .join(UserCourse, (
                (UserCourse.batch_id == Batch.id) &
                (UserCourse.course_id == Batch.course_id)
            ))
            .filter(
                UserCourse.user_id == user.id,
                Programme.is_active == True,
            )
            .distinct()
            .order_by(Programme.display_order)
        )
        programmes = result.scalars().all()

    data = []
    for p in programmes:
        # Count courses in this programme
        course_count_res = await db.execute(
            select(func.count()).select_from(ProgrammeCourse).filter(ProgrammeCourse.programme_id == p.id)
        )
        course_count = course_count_res.scalar() or 0

        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "icon": p.icon,
            "color": p.color,
            "isActive": p.is_active,
            "displayOrder": p.display_order,
            "courseCount": course_count,
        })
    return data
