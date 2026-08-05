# ============================================================
# Coordinator & Admin routes — optimized with SQL aggregations
# ============================================================
# - All queries use SQL aggregations (no Python loops over students)
# - Student listing is paginated (default 50 per page)
# - Role-based access: coordinator sees own college, admin sees all
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, literal
import io
from fastapi.responses import StreamingResponse
import openpyxl

from dashboard_common import (
    DEFAULT_TUTORIAL_COUNT,
    PROGRESS_SERIES,
    STATUS_SERIES,
    chart_series,
    course_xp_sum,
    initials as build_initials,
    progress_bucket,
)
from database import get_db
from cache import get_cached, set_cached
from models import User, College, UserCourse, UserTutorial, Tutorial
from dependencies import require_coordinator, require_college_access
from services.feedback_summary import build_feedback_summary

router = APIRouter(prefix="/api/coordinator", tags=["coordinator"])


async def _fetch_summary_stats(
    db: AsyncSession,
    course_id: str = "linux",
    batch_id: str | None = None,
    college_id: str | None = None,
    total_tutorials: int | None = None,
) -> dict[str, dict]:
    """
    Per-college aggregate stats for a course/batch in ONE SQL statement for ALL colleges
    (was 3 queries PER college). Returns {college_id: stats_dict} of pure JSON-able data,
    so the result is cache-friendly (see Phase 4).

    Status-bucket precedence + thresholds mirror the legacy per-student Python logic
    exactly (completed > active > at_risk > inactive). XP is course-scoped (matching the
    legacy avg-XP query), which is why the previously-redundant XP re-query is dropped.

    `total_tutorials` may be passed in by a caller that already computed it, to avoid a
    duplicate COUNT; otherwise it is fetched here.
    """
    if total_tutorials is None:
        tot_tut_res = await db.execute(
            select(func.count(Tutorial.id)).filter(Tutorial.course_id == course_id)
        )
        total_tutorials = tot_tut_res.scalar() or DEFAULT_TUTORIAL_COUNT
    T = total_tutorials
    # int(T*0.3) == the Python float threshold `watched > T*0.3` for integer watched counts.
    watched_thresh = int(T * 0.3)

    # ── Inner: one row per in-scope student, with course-scoped aggregates. ──
    per_student = (
        select(
            User.id.label("uid"),
            User.college_id.label("college_id"),
            # Course-scoped XP: only sum xp from THIS course's tutorials (Tutorial.id
            # is non-NULL only when the outer-joined tutorial matched course_id).
            course_xp_sum().label("xp"),
            func.count(case((UserTutorial.watched == True, Tutorial.id), else_=None)).label("watched"),
            func.count(case((UserTutorial.practiced == True, Tutorial.id), else_=None)).label("completed"),
            func.count(case((UserTutorial.minitask_opted == True, Tutorial.id), else_=None)).label("minitasks"),
        )
        .select_from(User)
        .join(UserCourse, UserCourse.user_id == User.id)
        .outerjoin(UserTutorial, UserTutorial.user_id == User.id)
        .outerjoin(Tutorial, (Tutorial.id == UserTutorial.tutorial_id) & (Tutorial.course_id == course_id))
        .filter(
            User.role == "student",
            User.is_test_account != True,
            UserCourse.course_id == course_id,
            User.college_id.isnot(None),
        )
        .group_by(User.id, User.college_id)
    )
    if batch_id:
        per_student = per_student.filter(UserCourse.batch_id == batch_id)
    if college_id:
        per_student = per_student.filter(User.college_id == college_id)
    sub = per_student.subquery("per_student")

    # ── Outer: per-college bucket counts (mutually exclusive, precedence-preserving). ──
    is_completed = sub.c.completed >= T
    is_active = (sub.c.completed < T) & (sub.c.watched > watched_thresh)
    is_at_risk = (sub.c.completed < T) & (sub.c.watched <= watched_thresh) & (sub.c.watched > 0)
    is_inactive = (sub.c.completed < T) & (sub.c.watched == 0)

    stats_q = (
        select(
            sub.c.college_id.label("college_id"),
            func.count().label("total"),
            func.sum(case((is_completed, 1), else_=0)).label("num_completed"),
            func.sum(case((is_active, 1), else_=0)).label("num_active"),
            func.sum(case((is_at_risk, 1), else_=0)).label("num_at_risk"),
            func.sum(case((is_inactive, 1), else_=0)).label("num_inactive"),
            func.sum(case((sub.c.minitasks > 0, 1), else_=0)).label("with_minitasks"),
            func.sum(sub.c.xp).label("total_xp"),
            func.sum(func.round(sub.c.completed * 100.0 / literal(T))).label("progress_sum"),
        )
        .group_by(sub.c.college_id)
    )
    rows = (await db.execute(stats_q)).all()

    stats: dict[str, dict] = {}
    for r in rows:
        total = r.total or 0
        if total == 0:
            continue
        num_completed = r.num_completed or 0
        num_active = r.num_active or 0
        stats[str(r.college_id)] = {
            "totalStudents": total,
            "activeStudents": num_active + num_completed,
            "inactiveStudents": r.num_inactive or 0,
            "atRiskStudents": r.num_at_risk or 0,
            "completedStudents": num_completed,
            "avgProgress": round(float(r.progress_sum or 0) / total),
            "avgXP": round(float(r.total_xp or 0) / total),
            "completionRate": round((num_completed / total) * 100),
            "studentsWithMinitasks": r.with_minitasks or 0,
        }
    return stats


async def _build_college_summary(
    db: AsyncSession,
    college_id: str | None = None,
    course_id: str = "linux",
    batch_id: str | None = None,
    total_tutorials: int | None = None,
) -> list[dict]:
    """
    Builds college summaries. College metadata (name/location/order) comes from one query;
    all per-college stats come from a single aggregate (see _fetch_summary_stats).
    Total: 3 queries regardless of college count (was 2 + 3N).
    """
    # College metadata + ordering — same set/order as before.
    if college_id:
        result = await db.execute(select(College).filter(College.id == college_id))
        colleges = result.scalars().all()
    else:
        college_query = (
            select(College)
            .join(User, User.college_id == College.id)
            .join(UserCourse, UserCourse.user_id == User.id)
            .filter(
                User.role == "student",
                User.is_test_account != True,
                UserCourse.course_id == course_id,
            )
        )
        if batch_id:
            college_query = college_query.filter(UserCourse.batch_id == batch_id)
        college_query = college_query.distinct().order_by(College.name)
        colleges = (await db.execute(college_query)).scalars().all()

    stats = await _fetch_summary_stats(
        db, course_id=course_id, batch_id=batch_id, college_id=college_id,
        total_tutorials=total_tutorials,
    )

    summaries = []
    for college in colleges:
        cid = str(college.id)
        s = stats.get(cid)
        if not s:
            # Matches the legacy zero-branch shape (no studentsWithMinitasks key).
            summaries.append({
                "id": cid,
                "name": college.name,
                "location": college.location or "",
                "coordinatorName": college.coordinator_name or "",
                "course": course_id,
                "totalCourseStudents": 0,
                "totalStudents": 0,
                "activeStudents": 0,
                "inactiveStudents": 0,
                "atRiskStudents": 0,
                "completedStudents": 0,
                "avgProgress": 0,
                "avgXP": 0,
                "completionRate": 0,
            })
            continue
        summaries.append({
            "id": cid,
            "name": college.name,
            "location": college.location or "",
            "coordinatorName": college.coordinator_name or "",
            "course": course_id,
            "totalCourseStudents": s["totalStudents"],
            "totalStudents": s["totalStudents"],
            "activeStudents": s["activeStudents"],
            "inactiveStudents": s["inactiveStudents"],
            "atRiskStudents": s["atRiskStudents"],
            "completedStudents": s["completedStudents"],
            "avgProgress": s["avgProgress"],
            "avgXP": s["avgXP"],
            "completionRate": s["completionRate"],
            "studentsWithMinitasks": s["studentsWithMinitasks"],
        })

    return summaries


async def _get_student_rows(
    db: AsyncSession,
    college_id: str,
    course_id: str = "linux",
    batch_id: str | None = None,
    page: int = 1,
    limit: int = 50,
    sort: str = "progress",
    status_filter: str = "all",
    search: str = "",
    total_tutorials: int | None = None,
):
    """
    Returns paginated student rows for a specific college and course/batch.

    `total_tutorials` may be passed in by a caller that already computed it, to avoid a
    duplicate COUNT; otherwise it is fetched here.
    """
    if total_tutorials is None:
        tot_tut_res = await db.execute(select(func.count(Tutorial.id)).filter(Tutorial.course_id == course_id))
        total_tutorials = tot_tut_res.scalar() or DEFAULT_TUTORIAL_COUNT

    # ── Step 1: Build the student IDs query (filtered by college, course, batch) ──
    stu_id_query = select(User.id).filter(
        User.college_id == college_id,
        User.role == "student",
        User.is_test_account != True
    )
    stu_id_query = stu_id_query.join(UserCourse, UserCourse.user_id == User.id).filter(UserCourse.course_id == course_id)
    if batch_id:
        stu_id_query = stu_id_query.filter(UserCourse.batch_id == batch_id)
        
    stu_ids_res = await db.execute(stu_id_query)
    student_ids = stu_ids_res.scalars().all()

    # ── Step 2: Build the aggregation query ──
    watched_col = func.count(
        case((UserTutorial.watched == True, Tutorial.id), else_=None)
    ).label("tutorials_watched")

    completed_col = func.count(
        case((UserTutorial.practiced == True, Tutorial.id), else_=None)
    ).label("tutorials_completed")

    minitask_col = func.count(
        case((UserTutorial.minitask_opted == True, Tutorial.id), else_=None)
    ).label("minitasks_opted")

    progress_col = case(
        (literal(total_tutorials) > 0,
         func.round(
             func.count(
                 case((UserTutorial.practiced == True, Tutorial.id), else_=None)
             ) * 100.0 / literal(total_tutorials)
         )),
        else_=literal(0),
    ).label("progress")

    status_col = case(
        (func.count(
            case((UserTutorial.practiced == True, Tutorial.id), else_=None)
         ) >= literal(total_tutorials), literal("completed")),
        (func.count(
            case((UserTutorial.watched == True, Tutorial.id), else_=None)
         ) > literal(int(total_tutorials * 0.3)), literal("active")),
        (func.count(
            case((UserTutorial.watched == True, Tutorial.id), else_=None)
         ) > literal(0), literal("at_risk")),
        (course_xp_sum() > 0, literal("inactive")),
        else_=literal("not_started"),
    ).label("status")

    base = select(
        User.id,
        User.display_name,
        User.username,
        course_xp_sum().label("xp_total"),
        watched_col,
        completed_col,
        minitask_col,
        progress_col,
        status_col,
    ).outerjoin(
        UserTutorial, UserTutorial.user_id == User.id
    ).outerjoin(
        Tutorial,
        (Tutorial.id == UserTutorial.tutorial_id) & (Tutorial.course_id == course_id)
    ).filter(
        User.id.in_(student_ids)
    ).group_by(User.id)

    # Search filter (applied before aggregation since it's on User columns)
    if search:
        base = base.filter(
            User.display_name.ilike(f"%{search}%") |
            User.username.ilike(f"%{search}%")
        )

    # Wrap as a subquery so we can filter/sort by computed columns
    sub = base.subquery("student_stats")

    # ── Step 2: Build the outer query with filtering, sorting, pagination ──
    outer = select(sub)

    # Status filter — done in SQL WHERE, not Python
    if status_filter != "all":
        if status_filter == "inactive":
            outer = outer.where(sub.c.status.in_(["inactive", "not_started"]))
        else:
            outer = outer.where(sub.c.status == status_filter)

    # ── Step 3: Get TOTAL count (for pagination metadata) before LIMIT ──
    count_q = select(func.count()).select_from(outer.subquery("filtered"))
    total_count = (await db.execute(count_q)).scalar() or 0
    total_pages = max(1, (total_count + limit - 1) // limit)

    # ── Step 4: Sort in SQL — always with a unique tiebreaker (sub.c.id) so pagination is
    # stable. Without it, ties on a non-unique column (e.g. the many students at 0%
    # progress) have no defined order, and a student could repeat on two pages or be
    # skipped between requests. ──
    if sort == "xp":
        primary = sub.c.xp_total.desc()
    elif sort == "name":
        primary = func.coalesce(sub.c.display_name, sub.c.username)
    elif sort == "tasks":
        primary = sub.c.minitasks_opted.desc()
    else:  # progress (default)
        primary = sub.c.progress.desc()
    outer = outer.order_by(primary, sub.c.id)

    # ── Step 5: REAL pagination — PostgreSQL only processes these rows ──
    offset = (page - 1) * limit
    outer = outer.limit(limit).offset(offset)

    res = await db.execute(outer)
    rows = res.all()

    # ── Step 6: Build response dicts (no computation, just formatting) ──
    students = []
    for row in rows:
        uid = row.id
        name = row.display_name
        username = row.username

        initials = build_initials(name, username)

        students.append({
            "id": str(uid),
            "name": name or username or "",
            "initials": initials,
            "rollNo": "",  # Not in DB yet — placeholder
            "tutorialsWatched": row.tutorials_watched,
            "tutorialsCompleted": row.tutorials_completed,
            "minitasksOpted": row.minitasks_opted,
            "totalTutorials": total_tutorials,
            "progress": int(row.progress),
            "xp": row.xp_total,
            "lastActive": "—",  # Not tracked yet — placeholder
            "status": row.status,
        })

    return {
        "students": students,
        "pagination": {
            "currentPage": page,
            "totalPages": total_pages,
            "totalRecords": total_count,
            "limit": limit,
        }
    }


# ===== ROUTES =====


@router.get("/public/list")
async def get_public_colleges(db: AsyncSession = Depends(get_db)):
    """Publicly accessible list of colleges for the login dropdown."""
    result = await db.execute(select(College.id, College.name).order_by(College.name))
    return [{"id": row.id, "name": row.name} for row in result.all()]


@router.get("/colleges")
async def get_all_colleges(
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    user: User = Depends(require_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all colleges with computed metrics for a course/batch.
    """
    college_id = None
    if user.effective_role == "coordinator":
        college_id = user.college_id
        # A coordinator with no assigned college would otherwise fall through with
        # college_id=None, which _build_college_summary reads as "every college".
        if not college_id:
            raise HTTPException(
                status_code=403,
                detail="No college is assigned to your account",
            )

    cache_key = f"coord:colleges:{college_id or 'all'}:{course_id}:{batch_id or 'all'}"
    cached = await get_cached(cache_key)
    if cached is not None:
        return cached

    result = await _build_college_summary(db, college_id=college_id, course_id=course_id, batch_id=batch_id)
    await set_cached(cache_key, result, ttl=120)
    return result


@router.get("/colleges/{college_id}")
async def get_college_details(
    college_id: str,
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("progress"),
    status: str = Query("all"),
    search: str = Query(""),
    user: User = Depends(require_college_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a specific college's details + paginated student list for a course/batch.
    """
    # Compute the tutorial count once and share it across the summary aggregate and the
    # student-rows query (avoids two duplicate COUNTs). The summary's own College fetch
    # doubles as the existence check, so the separate College query is gone.
    total_tutorials = (await db.execute(
        select(func.count(Tutorial.id)).filter(Tutorial.course_id == course_id)
    )).scalar() or DEFAULT_TUTORIAL_COUNT

    # The summary block is invariant to page/sort/search/status — cache it so paging and
    # searching a college don't re-run the aggregate. Student rows are NOT cached.
    summary_key = f"coord:summary:{college_id}:{course_id}:{batch_id or 'all'}"
    summary = await get_cached(summary_key)
    if summary is None:
        summary = await _build_college_summary(
            db, college_id=college_id, course_id=course_id, batch_id=batch_id,
            total_tutorials=total_tutorials,
        )
        if not summary:
            raise HTTPException(status_code=404, detail="College not found")
        await set_cached(summary_key, summary, ttl=120)

    student_data = await _get_student_rows(
        db, college_id, course_id=course_id, batch_id=batch_id,
        page=page, limit=limit, sort=sort,
        status_filter=status, search=search,
        total_tutorials=total_tutorials,
    )

    s = summary[0]
    return {
        "college": {
            "id": s["id"],
            "name": s["name"],
            "location": s["location"],
            "coordinatorName": s["coordinatorName"],
            "course": course_id,
        },
        "metrics": {
            "totalStudents": s["totalStudents"],
            "activeStudents": s["activeStudents"],
            "completedStudents": s["completedStudents"],
            "avgProgress": s["avgProgress"],
            "avgXP": s["avgXP"],
            "completionRate": s["completionRate"],
        },
        # Per-status counts for the WHOLE cohort (not the current page). The UI's status
        # chips must show these; counting the paginated `students` array gave wrong totals
        # like "All (10)" for a 200-learner college. Note: summary.activeStudents already
        # includes completed, so the strict "active" bucket subtracts completed back out.
        "statusCounts": {
            "all": s["totalStudents"],
            "active": s["activeStudents"] - s["completedStudents"],
            "completed": s["completedStudents"],
            "at_risk": s["atRiskStudents"],
            "inactive": s["inactiveStudents"],
        },
        "students": student_data["students"],
        "pagination": student_data["pagination"],
    }


@router.get("/colleges/{college_id}/export")
async def export_college_students(
    college_id: str,
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    user: User = Depends(require_college_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Exports a list of all students and their progress to an Excel file.
    """
    # Fetch max students for export
    student_data = await _get_student_rows(
        db, college_id, course_id=course_id, batch_id=batch_id,
        page=1, limit=10000, sort="progress",
        status_filter="all", search="",
    )

    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Student Progress"

    # ── Column config: (header, width) ──
    columns = [
        ("S.No.", 10),
        ("Student Name", 35),
        ("Progress Percentage", 25),
        ("Tutorials Completed", 25),
        ("Mini-Tasks Opted", 22),
    ]

    # Set column widths
    for col_idx, (_, width) in enumerate(columns, start=1):
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        sheet.column_dimensions[col_letter].width = width

    # ── Header row ──
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")

    for col_idx, (title, _) in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=col_idx, value=title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
    sheet.row_dimensions[1].height = 28

    # ── Styling helpers ──
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center", indent=1)
    even_fill = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")

    # ── Data rows ──
    for index, student in enumerate(student_data["students"], start=1):
        row_num = index + 1  # row 1 is header
        row_data = [
            index,
            student["name"],
            f"{student['progress']}%",
            f"{student['tutorialsCompleted']}/{student['totalTutorials']}",
            student.get("minitasksOpted", 0),
        ]
        for col_idx, value in enumerate(row_data, start=1):
            cell = sheet.cell(row=row_num, column=col_idx, value=value)
            cell.border = thin_border
            cell.alignment = left_align if col_idx == 2 else center_align
            if index % 2 == 0:
                cell.fill = even_fill
        sheet.row_dimensions[row_num].height = 22

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    res_col = await db.execute(select(College.name).filter(College.id == college_id))
    college = res_col.scalars().first()
    cname = college.replace(" ", "_").replace(",", "") if college else "College"

    resp_headers = {
        "Content-Disposition": f'attachment; filename="{cname}_Students_Report.xlsx"'
    }
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=resp_headers,
    )


@router.get("/colleges/{college_id}/analytics")
async def get_college_analytics(
    college_id: str,
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    user: User = Depends(require_college_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns deep analytics arrays (status distribution, top performers, etc.)
    for the exact college. Fetches and aggregates all students natively.
    """
    cache_key = f"coord:analytics:{college_id}:{course_id}:{batch_id or 'all'}"
    cached = await get_cached(cache_key)
    if cached is not None:
        return cached

    # ── Step 1: Filter students by enrollment in course & batch ──
    stu_query = select(User.id).filter(
        User.college_id == college_id,
        User.role == "student",
        User.is_test_account != True
    )
    stu_query = stu_query.join(UserCourse, UserCourse.user_id == User.id).filter(UserCourse.course_id == course_id)
    if batch_id:
        stu_query = stu_query.filter(UserCourse.batch_id == batch_id)

    stu_ids_res = await db.execute(stu_query)
    student_ids = stu_ids_res.scalars().all()
    total = len(student_ids)

    # Handle empty state gracefully
    if total == 0:
        return {
            "totalStudents": 0,
            "avgProgress": 0,
            "avgWatched": 0,
            "totalTutorials": 0,
            "avgXP": 0,
            "totalXP": 0,
            "statusData": chart_series(STATUS_SERIES, [0] * len(STATUS_SERIES)),
            "progressData": chart_series(PROGRESS_SERIES, [0] * len(PROGRESS_SERIES)),
            "tutorialCompletion": [],
            "topPerformers": [],
            "atRisk": []
        }

    # Tutorial titles and per-tutorial completion counts in one pass. The outer join keeps
    # tutorials nobody has finished, which the completion chart still has to plot at 0%,
    # and total_tutorials falls out of the row count.
    tuts_res = await db.execute(
        select(
            Tutorial.tutorial_number,
            Tutorial.title,
            func.count(UserTutorial.user_id).label("completed_count"),
        )
        .select_from(Tutorial)
        .outerjoin(
            UserTutorial,
            (UserTutorial.tutorial_id == Tutorial.id)
            & (UserTutorial.practiced == True)
            & (UserTutorial.user_id.in_(student_ids)),
        )
        .filter(Tutorial.course_id == course_id)
        .group_by(Tutorial.tutorial_number, Tutorial.title)
        .order_by(Tutorial.tutorial_number)
    )
    tuts_data = tuts_res.all()
    tuts_map = {row.tutorial_number: row.title for row in tuts_data}
    tut_counts = {row.tutorial_number: row.completed_count for row in tuts_data}
    total_tutorials = len(tuts_data) or DEFAULT_TUTORIAL_COUNT

    student_metrics_res = await db.execute(
        select(
            User.id,
            User.display_name,
            User.username,
            course_xp_sum().label("xp_total"),
            func.count(
                case((UserTutorial.watched == True, Tutorial.id), else_=None)
            ).label("watched"),
            func.count(
                case((UserTutorial.practiced == True, Tutorial.id), else_=None)
            ).label("completed"),
        ).outerjoin(
            UserTutorial, UserTutorial.user_id == User.id
        ).outerjoin(
            Tutorial,
            (Tutorial.id == UserTutorial.tutorial_id) & (Tutorial.course_id == course_id)
        ).filter(
            User.id.in_(student_ids)
        ).group_by(User.id)
    )
    students = student_metrics_res.all()

    status_counts = {"completed": 0, "active": 0, "at_risk": 0, "inactive": 0}
    progress_counts = [0] * len(PROGRESS_SERIES)

    total_watched = 0
    total_xp = 0
    total_progress = 0

    all_students_mapped = []

    for uid, name, username, xp, watched, completed in students:
        progress = round((completed / total_tutorials) * 100)
        total_watched += watched
        total_xp += xp
        total_progress += progress

        if completed >= total_tutorials:
            status = "completed"
        elif watched > total_tutorials * 0.3:
            status = "active"
        elif watched > 0:
            status = "at_risk"
        else:
            status = "inactive"

        status_counts[status] += 1
        progress_counts[progress_bucket(progress)] += 1

        all_students_mapped.append({
            "id": str(uid),
            "name": name or username or "",
            "initials": build_initials(name, username),
            "xp": xp,
            "progress": progress,
            "tutorialsWatched": watched,
            "tutorialsCompleted": completed,
            "totalTutorials": total_tutorials,
            "status": status,
            "lastActive": "—"
        })

    top_performers = sorted(
        (s for s in all_students_mapped if s["xp"] > 0),
        key=lambda s: s["xp"],
        reverse=True,
    )[:5]

    # The ladder above only ever assigns these four statuses, so the "not_started" case the
    # previous filter allowed for — and the has_any_activity flag that gated it — could
    # never match anything.
    at_risk_list = sorted(
        (s for s in all_students_mapped if s["status"] in ("at_risk", "inactive")),
        key=lambda s: s["progress"],
    )

    tutorial_completion = [
        {
            "number": i,
            "title": tuts_map.get(i, f"Tutorial {i}"),
            "completedCount": tut_counts.get(i, 0),
            "rate": round((tut_counts.get(i, 0) / total) * 100),
        }
        for i in range(1, total_tutorials + 1)
    ]

    result = {
        "totalStudents": total,
        "avgProgress": round(total_progress / total),
        "avgWatched": round(total_watched / total, 1),
        "totalTutorials": total_tutorials,
        "avgXP": round(total_xp / total),
        "totalXP": total_xp,
        "statusData": chart_series(STATUS_SERIES, [
            status_counts["completed"],
            status_counts["active"],
            status_counts["at_risk"],
            status_counts["inactive"],
        ]),
        "progressData": chart_series(PROGRESS_SERIES, progress_counts),
        "tutorialCompletion": tutorial_completion,
        "topPerformers": top_performers,
        "atRisk": at_risk_list
    }
    await set_cached(cache_key, result, ttl=300)
    return result


# ============================================================
# Coordinator Feedback Summary (College-scoped)
# ============================================================

@router.get("/colleges/{college_id}/feedback-summary")
async def get_coordinator_feedback_summary(
    college_id: str,
    tutorial_id: Optional[str] = Query(None, description="Filter by tutorial UUID"),
    step_type: Optional[str] = Query(None, description="Filter by step type"),
    reason: Optional[str] = Query(None, description="Filter by reason key"),
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    user: User = Depends(require_college_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Feedback analytics for a coordinator's college.
    Same shape as admin feedback-summary, but hard-filtered to the given college.
    Coordinators can only access their own college.
    """
    cache_key = (
        f"fb:{college_id}:{course_id}:{batch_id or '-'}:"
        f"{tutorial_id or '-'}:{step_type or '-'}:{reason or '-'}"
    )
    cached = await get_cached(cache_key)
    if cached is not None:
        return cached

    result = await build_feedback_summary(
        db,
        course_id=course_id,
        college_id=college_id,
        batch_id=batch_id,
        tutorial_id=tutorial_id,
        step_type=step_type,
        reason=reason,
    )
    await set_cached(cache_key, result, ttl=120)
    return result

