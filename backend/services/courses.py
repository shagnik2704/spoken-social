# ============================================================
# Course listing — shared by /api/me and /api/courses/me
# ============================================================
# Both endpoints answer "which courses does this user see?" and had grown byte-identical
# copies of the admin and coordinator branches, including the batch-shaping loop below,
# which appeared four times across routes/user.py and routes/course.py.
#
# The student branch is deliberately NOT here: /api/me reads the already-eager-loaded
# User.courses relationship (it needs it for to_api_dict anyway), while /api/courses/me
# queries UserCourse directly. Same result, different data source, no duplication worth
# collapsing.
# ============================================================

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import CollegeCourse, Course


def shape_course_with_batches(course, programme_id: Optional[str] = None) -> dict:
    """
    A course dict plus its batches, with the active batch (or the first, or none) hoisted
    onto batchId/batchName/batchStatus for the course switcher.
    """
    data = (
        course.to_api_dict()
        if hasattr(course, "to_api_dict")
        else {"id": course.id, "title": course.title, "description": course.description}
    )
    batches = (
        [b for b in course.batches if b.programme_id == programme_id]
        if programme_id
        else course.batches
    )
    data["batches"] = [b.to_api_dict() for b in batches]

    active = next((b for b in batches if b.status == "active"), batches[0] if batches else None)
    if active:
        data["batchId"] = str(active.id)
        data["batchName"] = active.name
        data["batchStatus"] = active.computed_status
    else:
        data["batchId"] = None
        data["batchName"] = None
        data["batchStatus"] = "inactive"
    return data


async def list_admin_courses(db: AsyncSession, programme_id: Optional[str] = None) -> list[dict]:
    """Every course on the platform, optionally narrowed to one programme."""
    query = select(Course).options(selectinload(Course.batches))
    if programme_id:
        from models.programme import ProgrammeCourse

        query = query.join(
            ProgrammeCourse, ProgrammeCourse.course_id == Course.id
        ).filter(ProgrammeCourse.programme_id == programme_id)
    query = query.order_by(Course.title)

    courses = (await db.execute(query)).scalars().all()
    return [shape_course_with_batches(c, programme_id) for c in courses]


async def list_college_courses(
    db: AsyncSession, college_id: Optional[str], programme_id: Optional[str] = None
) -> list[dict]:
    """Courses enabled for a coordinator's college."""
    query = (
        select(Course)
        .join(CollegeCourse, CollegeCourse.course_id == Course.id)
        .filter(CollegeCourse.college_id == college_id)
    )
    if programme_id:
        query = query.filter(CollegeCourse.programme_id == programme_id)
    query = query.options(selectinload(Course.batches)).order_by(Course.title)

    courses = (await db.execute(query)).scalars().all()
    return [shape_course_with_batches(c, programme_id) for c in courses]
