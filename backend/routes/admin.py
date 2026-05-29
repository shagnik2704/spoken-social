# ============================================================
# Admin routes — platform-wide aggregations + feedback analytics
# ============================================================
# 1. /platform-summary  — Overview + Analytics tab data
# 2. /feedback-summary   — Aggregated student feedback
# 3. /students/{id}/feedback — Per-student feedback detail
# ============================================================

from cache import get_cached,set_cached
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, case, cast, Date
from datetime import datetime, date
import calendar
import io
from fastapi.responses import StreamingResponse
import openpyxl

from database import get_db
from models import User, College, UserTutorial, Tutorial, UserCourse
from models.feedback import TutorialFeedback
from models.xp_event import XPEvent
from dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/platform-summary")
async def get_platform_summary(
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a single, pre-computed payload for the admin Overview + Analytics tabs.
    Now course and batch aware.
    """

    cache_key = f"admin:platform_summary:{course_id}:{batch_id or 'all'}:{state or 'all'}"
    cached = await get_cached(cache_key)
    if cached:
        return cached

    tot_tut_res = await db.execute(select(func.count(Tutorial.id)).filter(Tutorial.course_id == course_id))
    total_tutorials = tot_tut_res.scalar() or 20

    # ----- Per-student metrics (one query) -----
    query = select(
        User.id,
        User.display_name,
        User.username,
        func.coalesce(func.sum(UserTutorial.xp_earned), 0).label("xp_total"),
        User.college_id,
        func.count(
            case((UserTutorial.watched == True, Tutorial.id), else_=None)
        ).label("watched"),
        func.count(
            case((UserTutorial.practiced == True, Tutorial.id), else_=None)
        ).label("completed"),
        func.count(
            case((UserTutorial.minitask_opted == True, Tutorial.id), else_=None)
        ).label("minitasks_opted"),
    ).outerjoin(
        UserTutorial, UserTutorial.user_id == User.id
    ).outerjoin(
        Tutorial,
        (Tutorial.id == UserTutorial.tutorial_id) & (Tutorial.course_id == course_id)
    ).join(
        UserCourse, UserCourse.user_id == User.id
    ).filter(
        UserCourse.course_id == course_id
    )

    if batch_id:
        query = query.filter(UserCourse.batch_id == batch_id)

    if state:
        query = query.join(College, College.id == User.college_id).filter(
            User.role == "student",
            College.location.ilike(f"%{state}%")
        )
    else:
        query = query.filter(User.role == "student")

    query = query.group_by(User.id)
    res_metrics = await db.execute(query)
    student_metrics = res_metrics.all()

    # ----- Build college name lookup -----
    if state:
        colleges_res = await db.execute(select(College.id, College.name).filter(College.location.ilike(f"%{state}%")))
    else:
        colleges_res = await db.execute(select(College.id, College.name))
    colleges_loaded = colleges_res.all()
    college_names = {c.id: c.name for c in colleges_loaded}

    # ----- Compute derived metrics -----
    students_enriched = []
    status_counts = {"completed": 0, "active": 0, "at_risk": 0, "inactive": 0, "not_started": 0}
    progress_buckets = {"0": 0, "1-25": 0, "26-50": 0, "51-75": 0, "76-99": 0, "100": 0}
    total_progress = 0

    for row in student_metrics:
        uid, name, username, xp, college_id, watched, completed, minitasks_opted = row
        progress = round((completed / total_tutorials) * 100) if total_tutorials > 0 else 0
        total_progress += progress

        # Derive status
        if completed >= total_tutorials:
            status = "completed"
        elif watched > total_tutorials * 0.3:
            status = "active"
        elif watched > 0:
            status = "at_risk"
        else:
            status = "inactive" if xp > 0 else "not_started"

        status_counts[status] += 1

        # Progress buckets
        if progress == 0:
            progress_buckets["0"] += 1
        elif progress <= 25:
            progress_buckets["1-25"] += 1
        elif progress <= 50:
            progress_buckets["26-50"] += 1
        elif progress <= 75:
            progress_buckets["51-75"] += 1
        elif progress <= 99:
            progress_buckets["76-99"] += 1
        else:
            progress_buckets["100"] += 1

        # Build initials
        parts = (name or "").split()
        initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"

        students_enriched.append({
            "id": str(uid),
            "name": name or username or "",
            "initials": initials,
            "xp": xp,
            "progress": progress,
            "status": status,
            "watched": watched,
            "completed": completed,
            "minitasksOpted": minitasks_opted,
            "collegeName": college_names.get(college_id, "Unknown"),
        })

    total_students = len(students_enriched)
    avg_progress = round(total_progress / total_students) if total_students > 0 else 0
    avg_xp = round(sum(s["xp"] for s in students_enriched) / total_students) if total_students > 0 else 0
    completion_rate = round((status_counts["completed"] / total_students) * 100) if total_students > 0 else 0

    # ----- Top 10 performers by XP -----
    top_performers = sorted(students_enriched, key=lambda s: s["xp"], reverse=True)[:10]

    # ----- At-risk students (at_risk + inactive + not_started, sorted by lowest progress) -----
    at_risk = sorted(
        [s for s in students_enriched if s["status"] in ("at_risk", "inactive", "not_started")],
        key=lambda s: s["progress"],
    )[:10]

    # ----- Tutorial-wise completion rates -----
    # For each tutorial number, count how many students have completed it
    stats_query = select(
        Tutorial.tutorial_number,
        Tutorial.title,
        func.count(
            case((UserTutorial.practiced == True, UserTutorial.user_id), else_=None)
        ).label("completed_count"),
    ).outerjoin(
        UserTutorial, UserTutorial.tutorial_id == Tutorial.id
    )

    if state:
        stats_query = stats_query.join(User, User.id == UserTutorial.user_id).join(College, College.id == User.college_id).filter(
            Tutorial.course_id == course_id,
            User.role == "student",
            College.location.ilike(f"%{state}%")
        )
    else:
        stats_query = stats_query.filter(
            Tutorial.course_id == course_id
        )

    stats_query = stats_query.group_by(
        Tutorial.tutorial_number, Tutorial.title
    ).order_by(
        Tutorial.tutorial_number
    )
    res_stats = await db.execute(stats_query)
    tutorial_stats = res_stats.all()

    tutorial_completion = [
        {
            "number": t.tutorial_number,
            "name": t.title,
            "completedCount": t.completed_count,
            "rate": round((t.completed_count / total_students) * 100) if total_students > 0 else 0,
        }
        for t in tutorial_stats
    ]

    result = {
        "metrics": {
            "totalStudents": total_students,
            "totalColleges": len(colleges_loaded),
            "avgProgress": avg_progress,
            "avgXP": avg_xp,
            "completionRate": completion_rate,
            "totalCompleted": status_counts["completed"],
            "totalActive": status_counts["active"],
            "totalAtRisk": status_counts["at_risk"],
            "totalInactive": status_counts["inactive"] + status_counts["not_started"],
        },
        "statusDistribution": [
            {"name": "Completed", "value": status_counts["completed"], "color": "hsl(142, 76%, 36%)"},
            {"name": "Active", "value": status_counts["active"], "color": "hsl(221, 83%, 53%)"},
            {"name": "At Risk of Completion", "value": status_counts["at_risk"], "color": "hsl(38, 92%, 50%)"},
            {"name": "Inactive", "value": status_counts["inactive"] + status_counts["not_started"], "color": "hsl(0, 72%, 51%)"},
        ],
        "progressDistribution": [
            {"name": "0%", "value": progress_buckets["0"], "color": "hsl(0, 72%, 70%)"},
            {"name": "1–25%", "value": progress_buckets["1-25"], "color": "hsl(25, 95%, 60%)"},
            {"name": "26–50%", "value": progress_buckets["26-50"], "color": "hsl(38, 92%, 55%)"},
            {"name": "51–75%", "value": progress_buckets["51-75"], "color": "hsl(221, 83%, 60%)"},
            {"name": "76–99%", "value": progress_buckets["76-99"], "color": "hsl(142, 60%, 50%)"},
            {"name": "100%", "value": progress_buckets["100"], "color": "hsl(142, 76%, 36%)"},
        ],
        "topPerformers": top_performers,
        "atRiskStudents": at_risk,
        "tutorialCompletion": tutorial_completion,
    }
    await set_cached(cache_key, result)
    return result


@router.get("/minitask-analysis")
async def get_minitask_analysis(
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated minitask opt-in data by college and tutorial.
    """
    # Query all minitask opt-ins
    query = (
        select(
            College.name.label("college_name"),
            Tutorial.tutorial_number,
            func.count(UserTutorial.user_id).label("count")
        )
        .join(User, User.id == UserTutorial.user_id)
        .join(Tutorial, Tutorial.id == UserTutorial.tutorial_id)
        .join(UserCourse, UserCourse.user_id == User.id)
        .outerjoin(College, College.id == User.college_id)
        .filter(
            User.role == "student",
            UserTutorial.minitask_opted == True,
            Tutorial.course_id == course_id,
            UserCourse.course_id == course_id
        )
    )

    if batch_id:
        query = query.filter(UserCourse.batch_id == batch_id)
    
    query = query.group_by(College.name, Tutorial.tutorial_number).order_by(College.name, Tutorial.tutorial_number)
    
    res = await db.execute(query)
    rows = res.all()

    # Structure the data for frontend: {college_name: {tut_num: count}}
    analysis = {}
    for row in rows:
        cname = row.college_name or "Unknown"
        if cname not in analysis:
            analysis[cname] = {}
        analysis[cname][row.tutorial_number] = row.count

    return analysis




@router.get("/colleges/export")
async def export_all_colleges(
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Exports the macro view of all colleges and their stats to an Excel file.
    """
    # Import the same logic used to calculate their summary
    from routes.coordinator import _build_college_summary
    
    colleges_summary = await _build_college_summary(db, course_id=course_id, batch_id=batch_id)

    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Colleges Report"

    # ── Column config: (header, width) ──
    columns = [
        ("S.No.", 10),
        ("College Name", 45),
        ("Total Students Enrolled", 28),
        ("Active Students", 22),
        ("Fully Completed Students", 28),
        ("Students Opted for Minitasks", 30),
        ("Average Progress Percentage", 32),
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
    for index, col in enumerate(colleges_summary, start=1):
        row_num = index + 1
        row_data = [
            index,
            col["name"],
            col["totalCourseStudents"],
            col["activeStudents"],
            col["completedStudents"],
            col.get("studentsWithMinitasks", 0),
            f"{col['avgProgress']}%",
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

    headers_resp = {
        "Content-Disposition": 'attachment; filename="Platform_Colleges_Report.xlsx"'
    }
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers_resp,
    )


# ============================================================
# Mini-Task Opt-in Export
# ============================================================

@router.get("/minitask-students/export")
async def export_minitask_students(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Exports a flat list of all students who opted for mini-tasks.
    One row per (student, tutorial) pair where minitask_opted = True.
    Columns: S.No., Student Name, Email, College, Tutorial #, Tutorial Title
    Sorted by tutorial number, then student name.
    """
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    # Query all minitask opt-ins with student + tutorial + college info
    res = await db.execute(
        select(
            User.display_name,
            User.username,
            User.email,
            College.name.label("college_name"),
            Tutorial.tutorial_number,
            Tutorial.title.label("tutorial_title"),
        )
        .join(UserTutorial, UserTutorial.user_id == User.id)
        .join(Tutorial, Tutorial.id == UserTutorial.tutorial_id)
        .outerjoin(College, College.id == User.college_id)
        .filter(
            User.role == "student",
            UserTutorial.minitask_opted == True,
            Tutorial.course_id == "linux",
        )
        .order_by(Tutorial.tutorial_number, User.display_name)
    )
    rows = res.all()

    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Mini-Task Opt-ins"

    # Column config: (header, width)
    columns = [
        ("S.No.", 10),
        ("Student Name", 35),
        ("Email", 40),
        ("College", 45),
        ("Tutorial #", 14),
        ("Tutorial Title", 45),
    ]

    for col_idx, (_, width) in enumerate(columns, start=1):
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        sheet.column_dimensions[col_letter].width = width

    # Header row
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")

    for col_idx, (title, _) in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=col_idx, value=title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
    sheet.row_dimensions[1].height = 28

    # Styling helpers
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center", indent=1)
    even_fill = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")

    # Data rows
    for index, row in enumerate(rows, start=1):
        row_num = index + 1
        student_name = row.display_name or row.username or ""
        row_data = [
            index,
            student_name,
            row.email or "",
            row.college_name or "Unknown",
            row.tutorial_number,
            row.tutorial_title,
        ]
        for col_idx, value in enumerate(row_data, start=1):
            cell = sheet.cell(row=row_num, column=col_idx, value=value)
            cell.border = thin_border
            # Left-align name, email, college, tutorial title; center the rest
            cell.alignment = left_align if col_idx in (2, 3, 4, 6) else center_align
            if index % 2 == 0:
                cell.fill = even_fill
        sheet.row_dimensions[row_num].height = 22

    # Enable AutoFilter on all columns so admin can filter/sort directly in Excel
    last_row = len(rows) + 1  # header + data rows
    last_col = openpyxl.utils.get_column_letter(len(columns))
    sheet.auto_filter.ref = f"A1:{last_col}{last_row}"

    # Freeze the header row so it stays visible when scrolling
    sheet.freeze_panes = "A2"

    # ── Sheet 2: Unique Students (one row per student) ──
    sheet2 = wb.create_sheet(title="Unique Students")

    # Group rows by email
    from collections import OrderedDict
    student_map = OrderedDict()
    for row in rows:
        email = row.email or ""
        if email not in student_map:
            student_map[email] = {
                "name": row.display_name or row.username or "",
                "email": email,
                "college": row.college_name or "Unknown",
                "tutorials": [],
            }
        student_map[email]["tutorials"].append(
            f"{row.tutorial_number}. {row.tutorial_title}"
        )

    cols2 = [
        ("S.No.", 10),
        ("Student Name", 35),
        ("Email", 40),
        ("College", 45),
        ("Total Mini-Tasks", 18),
        ("Tutorials Opted", 70),
    ]

    for col_idx, (_, width) in enumerate(cols2, start=1):
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        sheet2.column_dimensions[col_letter].width = width

    for col_idx, (title, _) in enumerate(cols2, start=1):
        cell = sheet2.cell(row=1, column=col_idx, value=title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
    sheet2.row_dimensions[1].height = 28

    for index, (email, info) in enumerate(student_map.items(), start=1):
        row_num = index + 1
        tutorials_str = ", ".join(info["tutorials"])
        row_data = [
            index,
            info["name"],
            info["email"],
            info["college"],
            len(info["tutorials"]),
            tutorials_str,
        ]
        for col_idx, value in enumerate(row_data, start=1):
            cell = sheet2.cell(row=row_num, column=col_idx, value=value)
            cell.border = thin_border
            cell.alignment = left_align if col_idx in (2, 3, 4, 6) else center_align
            if index % 2 == 0:
                cell.fill = even_fill
        sheet2.row_dimensions[row_num].height = 22

    # AutoFilter + freeze on Sheet 2
    last_row2 = len(student_map) + 1
    last_col2 = openpyxl.utils.get_column_letter(len(cols2))
    sheet2.auto_filter.ref = f"A1:{last_col2}{last_row2}"
    sheet2.freeze_panes = "A2"

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    headers_resp = {
        "Content-Disposition": 'attachment; filename="MiniTask_OptIn_Report.xlsx"'
    }
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers_resp,
    )


# ============================================================
# College Daily Average XP (Line Chart Data)
# ============================================================

COLLEGE_COLORS = [
    "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
    "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
    "#14b8a6", "#e11d48", "#0ea5e9", "#a855f7", "#d946ef",
]


@router.get("/college-daily-xp")
async def get_college_daily_xp(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format, defaults to current"),
    college_ids: Optional[str] = Query(None, description="Comma-separated college IDs"),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns daily average XP per college for a given month.
    For each day, we compute: sum of XP that day per student, then average across students.
    """
    # Parse month
    if month:
        try:
            year, mo = int(month.split("-")[0]), int(month.split("-")[1])
        except (ValueError, IndexError):
            year, mo = datetime.now().year, datetime.now().month
    else:
        year, mo = datetime.now().year, datetime.now().month

    days_in_month = calendar.monthrange(year, mo)[1]
    month_start = date(year, mo, 1)
    if mo == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, mo + 1, 1)

    # Get colleges
    college_filter_ids = None
    if college_ids:
        college_filter_ids = [cid.strip() for cid in college_ids.split(",") if cid.strip()]

    colleges_query = select(College.id, College.name)
    if college_filter_ids:
        colleges_query = colleges_query.filter(College.id.in_(college_filter_ids))
    res_colleges = await db.execute(colleges_query.order_by(College.name))
    colleges = res_colleges.all()

    if not colleges:
        return {
            "month": f"{year:04d}-{mo:02d}",
            "daysInMonth": days_in_month,
            "colleges": [],
            "series": [{"day": d} for d in range(1, days_in_month + 1)],
        }

    college_list = []
    for i, c in enumerate(colleges):
        college_list.append({
            "id": c.id,
            "name": c.name,
            "color": COLLEGE_COLORS[i % len(COLLEGE_COLORS)],
        })

    # Subquery: per-student daily XP sum
    daily_student_xp = (
        select(
            User.college_id.label("college_id"),
            cast(XPEvent.created_at, Date).label("xp_date"),
            XPEvent.user_id.label("user_id"),
            func.sum(XPEvent.xp_delta).label("daily_xp"),
        )
        .join(User, XPEvent.user_id == User.id)
        .filter(
            User.role == "student",
            User.college_id.in_([c.id for c in colleges]),
            cast(XPEvent.created_at, Date) >= month_start,
            cast(XPEvent.created_at, Date) < month_end,
        )
        .group_by(User.college_id, cast(XPEvent.created_at, Date), XPEvent.user_id)
        .subquery()
    )

    # Main query: average daily XP per college per day
    result = await db.execute(
        select(
            daily_student_xp.c.college_id,
            daily_student_xp.c.xp_date,
            func.round(func.avg(daily_student_xp.c.daily_xp), 1).label("avg_xp"),
        )
        .group_by(daily_student_xp.c.college_id, daily_student_xp.c.xp_date)
        .order_by(daily_student_xp.c.xp_date)
    )
    rows = result.all()

    # Build series: one entry per day, with each college as a key
    series = []
    for day_num in range(1, days_in_month + 1):
        entry: dict = {"day": day_num}
        for c in colleges:
            entry[c.id] = 0
        series.append(entry)

    for row in rows:
        day_num = row.xp_date.day
        college_id = row.college_id
        avg_xp = float(row.avg_xp) if row.avg_xp else 0
        if 1 <= day_num <= days_in_month:
            series[day_num - 1][college_id] = avg_xp

    return {
        "month": f"{year:04d}-{mo:02d}",
        "daysInMonth": days_in_month,
        "colleges": college_list,
        "series": series,
    }


# ============================================================
# Feedback Analytics (Filterable)
# ============================================================

@router.get("/feedback-summary")
async def get_feedback_summary(
    tutorial_id: Optional[str] = Query(None, description="Filter by tutorial UUID"),
    step_type: Optional[str] = Query(None, description="Filter by step type"),
    reason: Optional[str] = Query(None, description="Filter by reason key"),
    college_id: Optional[str] = Query(None, description="Filter by college"),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Filterable feedback analytics for the admin panel.
    Returns:
    1. Filter options (tutorials, step types, reasons) for dropdowns
    2. Aggregated counts based on current filters
    3. Filtered entries grouped by tutorial, with student details
    """
    import uuid as uuid_mod

    # ----- Step 1: Fetch ALL tutorials for the filter dropdown -----
    res_all_tuts = await db.execute(
        select(Tutorial.id, Tutorial.title, Tutorial.tutorial_number)
        .filter(Tutorial.course_id == "linux")
        .order_by(Tutorial.tutorial_number)
    )
    all_tutorials = [
        {"id": str(t.id), "number": t.tutorial_number, "title": t.title}
        for t in res_all_tuts.all()
    ]

    # ----- Step 2: Build filtered query -----
    base_query = (
        select(TutorialFeedback)
        .options(selectinload(TutorialFeedback.user))
        .join(User, TutorialFeedback.user_id == User.id)
    )

    if tutorial_id:
        base_query = base_query.filter(TutorialFeedback.tutorial_id == uuid_mod.UUID(tutorial_id))
    if step_type:
        base_query = base_query.filter(TutorialFeedback.step_type == step_type)
    if college_id:
        base_query = base_query.filter(User.college_id == college_id)

    res_fb = await db.execute(base_query.order_by(TutorialFeedback.created_at.desc()))
    all_feedback = res_fb.scalars().all()

    # If reason filter is active, narrow down to entries containing that reason
    if reason:
        all_feedback = [fb for fb in all_feedback if reason in (fb.reasons or [])]

    # ----- Step 3: Aggregate counts -----
    reason_counts: dict[str, int] = {}
    step_type_counts: dict[str, int] = {}
    total_entries = len(all_feedback)

    for fb in all_feedback:
        step_type_counts[fb.step_type] = step_type_counts.get(fb.step_type, 0) + 1
        for r in (fb.reasons or []):
            reason_counts[r] = reason_counts.get(r, 0) + 1

    top_reasons = sorted(
        [{"key": k, "count": v, "percentage": round((v / total_entries) * 100) if total_entries > 0 else 0}
         for k, v in reason_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    step_breakdown = sorted(
        [{"stepType": k, "count": v} for k, v in step_type_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    # ----- Step 4: Build college name lookup -----
    college_ids = list({fb.user.college_id for fb in all_feedback if fb.user.college_id})
    if college_ids:
        res_cols = await db.execute(select(College.id, College.name).filter(College.id.in_(college_ids)))
        college_names = {c.id: c.name for c in res_cols.all()}
    else:
        college_names = {}

    # Tutorial info lookup
    tutorial_ids = list({fb.tutorial_id for fb in all_feedback})
    if tutorial_ids:
        res_tuts = await db.execute(
            select(Tutorial.id, Tutorial.title, Tutorial.tutorial_number)
            .filter(Tutorial.id.in_(tutorial_ids))
        )
        tut_map = {t.id: {"title": t.title, "number": t.tutorial_number} for t in res_tuts.all()}
    else:
        tut_map = {}

    # ----- Step 5: Build entries grouped by tutorial -----
    tutorial_groups: dict[str, dict] = {}

    for fb in all_feedback:
        tm = tut_map.get(fb.tutorial_id, {"title": "Unknown", "number": 0})
        tid = str(fb.tutorial_id)

        if tid not in tutorial_groups:
            tutorial_groups[tid] = {
                "tutorialId": tid,
                "tutorialNumber": tm["number"],
                "tutorialTitle": tm["title"],
                "studentCount": 0,
                "entries": [],
                "_student_ids": set(),
            }

        student_user = fb.user
        cid = student_user.college_id
        parts = (student_user.display_name or "").split()
        initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"

        tutorial_groups[tid]["entries"].append({
            "id": str(fb.id),
            "studentId": str(fb.user_id),
            "studentName": student_user.display_name or student_user.username,
            "studentInitials": initials,
            "collegeName": college_names.get(cid, "Unknown") if cid else "Unknown",
            "stepType": fb.step_type,
            "reasons": fb.reasons or [],
            "otherText": fb.other_text,
            "createdAt": fb.created_at.isoformat() if fb.created_at else None,
        })

        tutorial_groups[tid]["_student_ids"].add(str(fb.user_id))

    # Finalize: compute unique student counts & remove internal sets
    for tg in tutorial_groups.values():
        tg["studentCount"] = len(tg["_student_ids"])
        del tg["_student_ids"]

    sorted_groups = sorted(
        tutorial_groups.values(),
        key=lambda g: len(g["entries"]),
        reverse=True,
    )

    # ----- Step 6: Unique affected students count -----
    unique_students = len({str(fb.user_id) for fb in all_feedback})

    # ----- Step 7: All distinct reason keys for the filter dropdown -----
    # Fetch from ALL feedback (unfiltered) so dropdown always shows full list
    res_all_fb = await db.execute(select(TutorialFeedback.reasons))
    all_reason_lists = res_all_fb.scalars().all()
    all_reason_keys = set()
    for reasons_list in all_reason_lists:
        if reasons_list:
            all_reason_keys.update(reasons_list)
    all_reason_keys_sorted = sorted(all_reason_keys)

    return {
        "filterOptions": {
            "tutorials": all_tutorials,
            "stepTypes": ["watched", "practiced", "assignmentDone", "forumAsked", "forumAnswered"],
            "reasons": all_reason_keys_sorted,
        },
        "totalEntries": total_entries,
        "uniqueStudents": unique_students,
        "topReasons": top_reasons,
        "stepBreakdown": step_breakdown,
        "tutorialGroups": sorted_groups,
    }


@router.get("/students/{student_id}/feedback")
async def get_student_feedback(
    student_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns detailed feedback data for a single student:
    1. Student info (name, college, roll number)
    2. Summary stats (total issues, most common reason, most problematic step)
    3. Reason breakdown with counts
    4. All entries chronologically with tutorial details
    """
    import uuid as uuid_mod

    sid = uuid_mod.UUID(student_id)

    # Get the student
    res_st = await db.execute(select(User).filter_by(id=sid))
    student = res_st.scalars().first()
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")

    # Get college name
    college_name = "Unknown"
    if student.college_id:
        res_c = await db.execute(select(College.name).filter_by(id=student.college_id))
        college = res_c.first()
        if college:
            college_name = college.name

    # Build student info
    parts = (student.display_name or "").split()
    initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"

    student_info = {
        "id": str(student.id),
        "name": student.display_name or student.username,
        "initials": initials,
        "rollNo": student.username or "",
        "collegeName": college_name,
    }

    # Fetch all feedback for this student
    res_fe = await db.execute(
        select(TutorialFeedback)
        .filter(TutorialFeedback.user_id == sid)
        .order_by(TutorialFeedback.created_at.desc())
    )
    feedback_entries = res_fe.scalars().all()

    total = len(feedback_entries)

    if total == 0:
        return {
            "student": student_info,
            "totalEntries": 0,
            "summary": {
                "mostCommonReason": None,
                "mostProblematicStep": None,
            },
            "reasonBreakdown": [],
            "stepBreakdown": [],
            "entries": [],
            "tutorialGroups": [],
        }

    # Aggregate reasons and step types
    reason_counts: dict[str, int] = {}
    step_counts: dict[str, int] = {}

    for fb in feedback_entries:
        step_counts[fb.step_type] = step_counts.get(fb.step_type, 0) + 1
        for reason in (fb.reasons or []):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    # Sort by frequency
    reason_breakdown = sorted(
        [{"key": k, "count": v, "percentage": round((v / total) * 100) if total > 0 else 0}
         for k, v in reason_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    step_breakdown = sorted(
        [{"stepType": k, "count": v} for k, v in step_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    most_common_reason = reason_breakdown[0]["key"] if reason_breakdown else None
    most_problematic_step = step_breakdown[0]["stepType"] if step_breakdown else None

    # Build entries with tutorial info
    entries = []
    # Group by tutorial for the grouped view
    tutorial_groups: dict[str, dict] = {}

    tutorial_ids = list({fb.tutorial_id for fb in feedback_entries})
    if tutorial_ids:
        res_tuts = await db.execute(select(Tutorial.id, Tutorial.title, Tutorial.tutorial_number).filter(Tutorial.id.in_(tutorial_ids)))
        tut_map = {t.id: {"title": t.title, "number": t.tutorial_number} for t in res_tuts.all()}
    else:
        tut_map = {}

    for fb in feedback_entries:
        tm = tut_map.get(fb.tutorial_id, {"title": "Unknown", "number": 0})
        
        entry = {
            "id": str(fb.id),
            "tutorialId": str(fb.tutorial_id),
            "tutorialNumber": tm["number"],
            "tutorialTitle": tm["title"],
            "stepType": fb.step_type,
            "reasons": fb.reasons or [],
            "otherText": fb.other_text,
            "createdAt": fb.created_at.isoformat() if fb.created_at else None,
        }
        entries.append(entry)

        # Group by tutorial
        tid = str(fb.tutorial_id)
        if tid not in tutorial_groups:
            tutorial_groups[tid] = {
                "tutorialId": tid,
                "tutorialNumber": entry["tutorialNumber"],
                "tutorialTitle": entry["tutorialTitle"],
                "issueCount": 0,
                "entries": [],
            }
        tutorial_groups[tid]["issueCount"] += 1
        tutorial_groups[tid]["entries"].append(entry)

    # Sort tutorial groups by issue count (most problematic first)
    sorted_groups = sorted(
        tutorial_groups.values(),
        key=lambda g: g["issueCount"],
        reverse=True,
    )

    return {
        "student": student_info,
        "totalEntries": total,
        "summary": {
            "mostCommonReason": most_common_reason,
            "mostProblematicStep": most_problematic_step,
        },
        "reasonBreakdown": reason_breakdown,
        "stepBreakdown": step_breakdown,
        "entries": entries,
        "tutorialGroups": sorted_groups,
    }
