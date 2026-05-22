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
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, case, literal
import io
from fastapi.responses import StreamingResponse
import openpyxl

from database import get_db
from models import User, College, UserCourse, UserTutorial, Tutorial
from models.feedback import TutorialFeedback
from dependencies import get_current_user, require_coordinator, require_admin

router = APIRouter(prefix="/api/coordinator", tags=["coordinator"])


async def _build_college_summary(
    db: AsyncSession, 
    college_id: str | None = None,
    course_id: str = "linux",
    batch_id: str | None = None
) -> list[dict]:
    """
    Builds college summaries using individual SQL queries per college.
    Now course and batch aware.
    """
    if college_id:
        result = await db.execute(select(College).filter(College.id == college_id))
    else:
        result = await db.execute(select(College))
    colleges = result.scalars().all()

    tot_tut_res = await db.execute(select(func.count(Tutorial.id)).filter(Tutorial.course_id == course_id))
    total_tutorials = tot_tut_res.scalar() or 20

    summaries = []
    for college in colleges:
        # Get all student IDs for this college
        # Filter by enrollment in this course/batch if specified
        stu_query = select(User.id).filter(
            User.college_id == college.id,
            User.role == "student"
        )
        
        # Join with UserCourse to ensure they are enrolled in this course/batch
        stu_query = stu_query.join(UserCourse, UserCourse.user_id == User.id).filter(UserCourse.course_id == course_id)
        if batch_id:
            stu_query = stu_query.filter(UserCourse.batch_id == batch_id)

        stu_ids_res = await db.execute(stu_query)
        student_ids = stu_ids_res.scalars().all()
        total = len(student_ids)

        if total == 0:
            summaries.append({
                "id": str(college.id),
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

        # Per-student metrics via SQL
        student_metrics_query = select(
            User.id,
            User.xp_total,
            func.count(
                case((UserTutorial.watched == True, UserTutorial.tutorial_id), else_=None)
            ).label("watched"),
            func.count(
                case((UserTutorial.practiced == True, UserTutorial.tutorial_id), else_=None)
            ).label("completed"),
            func.count(
                case((UserTutorial.minitask_opted == True, UserTutorial.tutorial_id), else_=None)
            ).label("minitasks_opted"),
        ).outerjoin(
            UserTutorial, UserTutorial.user_id == User.id
        ).outerjoin(
            Tutorial,
            (Tutorial.id == UserTutorial.tutorial_id) & (Tutorial.course_id == course_id)
        ).filter(
            User.id.in_(student_ids) # Only students for this college/course/batch
        ).group_by(User.id)
        
        student_metrics_res = await db.execute(student_metrics_query)
        student_metrics = student_metrics_res.all()

        num_completed = 0
        num_active = 0
        num_at_risk = 0
        num_inactive = 0
        total_progress = 0
        students_with_minitasks = 0

        for row in student_metrics:
            uid, xp, watched_count, completed_count, minitasks_count = row
            progress = round((completed_count / total_tutorials) * 100) if total_tutorials > 0 else 0
            total_progress += progress

            if minitasks_count > 0:
                students_with_minitasks += 1

            if completed_count >= total_tutorials:
                num_completed += 1
            elif watched_count > total_tutorials * 0.3:
                num_active += 1
            elif watched_count > 0:
                num_at_risk += 1
            else:
                num_inactive += 1

        avg_xp_res = await db.execute(select(func.avg(User.xp_total)).filter(
            User.college_id == college.id,
            User.role == "student"
        ))
        avg_xp_val = avg_xp_res.scalar() or 0

        summaries.append({
            "id": str(college.id),
            "name": college.name,
            "location": college.location or "",
            "coordinatorName": college.coordinator_name or "",
            "course": course_id,
            "totalCourseStudents": total,
            "totalStudents": total,
            "activeStudents": num_active + num_completed,
            "inactiveStudents": num_inactive,
            "atRiskStudents": num_at_risk,
            "completedStudents": num_completed,
            "avgProgress": round(total_progress / total) if total > 0 else 0,
            "avgXP": round(float(avg_xp_val)),
            "completionRate": round((num_completed / total) * 100) if total > 0 else 0,
            "studentsWithMinitasks": students_with_minitasks,
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
    search: str = ""
):
    """
    Returns paginated student rows for a specific college and course/batch.
    """
    tot_tut_res = await db.execute(select(func.count(Tutorial.id)).filter(Tutorial.course_id == course_id))
    total_tutorials = tot_tut_res.scalar() or 20

    # ── Step 1: Build the student IDs query (filtered by college, course, batch) ──
    stu_id_query = select(User.id).filter(
        User.college_id == college_id,
        User.role == "student"
    )
    stu_id_query = stu_id_query.join(UserCourse, UserCourse.user_id == User.id).filter(UserCourse.course_id == course_id)
    if batch_id:
        stu_id_query = stu_id_query.filter(UserCourse.batch_id == batch_id)
        
    stu_ids_res = await db.execute(stu_id_query)
    student_ids = stu_ids_res.scalars().all()

    # ── Step 2: Build the aggregation query ──
    watched_col = func.count(
        case((UserTutorial.watched == True, UserTutorial.tutorial_id), else_=None)
    ).label("tutorials_watched")

    completed_col = func.count(
        case((UserTutorial.practiced == True, UserTutorial.tutorial_id), else_=None)
    ).label("tutorials_completed")

    minitask_col = func.count(
        case((UserTutorial.minitask_opted == True, UserTutorial.tutorial_id), else_=None)
    ).label("minitasks_opted")

    progress_col = case(
        (literal(total_tutorials) > 0,
         func.round(
             func.count(
                 case((UserTutorial.practiced == True, UserTutorial.tutorial_id), else_=None)
             ) * 100.0 / literal(total_tutorials)
         )),
        else_=literal(0),
    ).label("progress")

    status_col = case(
        (func.count(
            case((UserTutorial.practiced == True, UserTutorial.tutorial_id), else_=None)
         ) >= literal(total_tutorials), literal("completed")),
        (func.count(
            case((UserTutorial.watched == True, UserTutorial.tutorial_id), else_=None)
         ) > literal(int(total_tutorials * 0.3)), literal("active")),
        (func.count(
            case((UserTutorial.watched == True, UserTutorial.tutorial_id), else_=None)
         ) > literal(0), literal("at_risk")),
        (User.xp_total > 0, literal("inactive")),
        else_=literal("not_started"),
    ).label("status")

    base = select(
        User.id,
        User.display_name,
        User.username,
        User.xp_total,
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

    # ── Step 4: Sort in SQL ──
    if sort == "progress":
        outer = outer.order_by(sub.c.progress.desc())
    elif sort == "xp":
        outer = outer.order_by(sub.c.xp_total.desc())
    elif sort == "name":
        outer = outer.order_by(func.coalesce(sub.c.display_name, sub.c.username))
    elif sort == "tasks":
        outer = outer.order_by(sub.c.minitasks_opted.desc())
    else:
        outer = outer.order_by(sub.c.progress.desc())

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

        parts = (name or "").split()
        initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"

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

    return await _build_college_summary(db, college_id=college_id, course_id=course_id, batch_id=batch_id)


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
    user: User = Depends(require_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a specific college's details + paginated student list for a course/batch.
    """
    # Coordinator can only see their own college
    if user.effective_role == "coordinator" and str(user.college_id) != str(college_id):
        raise HTTPException(
            status_code=403,
            detail="You can only view your own college's students",
        )

    res = await db.execute(select(College).filter(College.id == college_id))
    college = res.scalars().first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    summary = await _build_college_summary(db, college_id=college_id, course_id=course_id, batch_id=batch_id)
    if not summary:
        raise HTTPException(status_code=404, detail="College not found")

    student_data = await _get_student_rows(
        db, college_id, course_id=course_id, batch_id=batch_id,
        page=page, limit=limit, sort=sort,
        status_filter=status, search=search,
    )

    return {
        "college": {
            "id": str(college.id),
            "name": college.name,
            "location": college.location or "",
            "coordinatorName": college.coordinator_name or "",
            "course": course_id,
        },
        "metrics": {
            "totalStudents": summary[0]["totalStudents"],
            "activeStudents": summary[0]["activeStudents"],
            "completedStudents": summary[0]["completedStudents"],
            "avgProgress": summary[0]["avgProgress"],
            "avgXP": summary[0]["avgXP"],
            "completionRate": summary[0]["completionRate"],
        },
        "students": student_data["students"],
        "pagination": student_data["pagination"],
    }


@router.get("/colleges/{college_id}/export")
async def export_college_students(
    college_id: str,
    course_id: str = Query("linux"),
    batch_id: Optional[str] = Query(None),
    user: User = Depends(require_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """
    Exports a list of all students and their progress to an Excel file.
    """
    if user.effective_role == "coordinator" and str(user.college_id) != str(college_id):
        raise HTTPException(
            status_code=403,
            detail="You can only export your own college's students",
        )

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
    user: User = Depends(require_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns deep analytics arrays (status distribution, top performers, etc.)
    for the exact college. Fetches and aggregates all students natively.
    """
    if user.role == "coordinator" and str(user.college_id) != str(college_id):
        raise HTTPException(
            status_code=403,
            detail="You can only view your own college's analytics",
        )

    tot_tut_res = await db.execute(select(func.count(Tutorial.id)).filter(Tutorial.course_id == "linux"))
    total_tutorials = tot_tut_res.scalar() or 20

    student_metrics_res = await db.execute(
        select(
            User.id,
            User.display_name,
            User.username,
            User.xp_total,
            func.count(
                case((UserTutorial.watched == True, UserTutorial.tutorial_id), else_=None)
            ).label("watched"),
            func.count(
                case((UserTutorial.practiced == True, UserTutorial.tutorial_id), else_=None)
            ).label("completed"),
        ).outerjoin(
            UserTutorial, UserTutorial.user_id == User.id
        ).outerjoin(
            Tutorial,
            (Tutorial.id == UserTutorial.tutorial_id) & (Tutorial.course_id == "linux")
        ).filter(
            User.college_id == college_id,
            User.role == "student"
        ).group_by(User.id)
    )
    students = student_metrics_res.all()
    total = len(students)

    status_counts = {"completed": 0, "active": 0, "at_risk": 0, "inactive": 0}
    progress_counts = {"0%": 0, "1–25%": 0, "26–50%": 0, "51–75%": 0, "76–99%": 0, "100%": 0}
    
    total_watched = 0
    total_xp = 0
    total_progress = 0
    
    all_students_mapped = []
    
    for row in students:
        uid, name, username, xp, watched, completed = row
        progress = round((completed / total_tutorials) * 100) if total_tutorials > 0 else 0
        total_watched += watched
        total_xp += xp
        total_progress += progress
        
        # Status calculation
        if completed >= total_tutorials:
            status = "completed"
            status_counts["completed"] += 1
        elif watched > total_tutorials * 0.3:
            status = "active"
            status_counts["active"] += 1
        elif watched > 0:
            status = "at_risk"
            status_counts["at_risk"] += 1
        else:
            status = "inactive"
            status_counts["inactive"] += 1
            
        # Progress calculation
        if progress == 0: progress_counts["0%"] += 1
        elif progress <= 25: progress_counts["1–25%"] += 1
        elif progress <= 50: progress_counts["26–50%"] += 1
        elif progress <= 75: progress_counts["51–75%"] += 1
        elif progress <= 99: progress_counts["76–99%"] += 1
        else: progress_counts["100%"] += 1
            
        display = name or username or ""
        parts = display.split()
        initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"
            
        all_students_mapped.append({
            "id": str(uid),
            "name": display,
            "initials": initials,
            "xp": xp,
            "progress": progress,
            "tutorialsWatched": watched,
            "tutorialsCompleted": completed,
            "totalTutorials": total_tutorials,
            "status": status,
            "lastActive": "—"
        })

    # Sort top performers
    sorted_by_xp = sorted(all_students_mapped, key=lambda x: x["xp"], reverse=True)
    top_performers = sorted_by_xp[:5]
    
    # Sort at risk
    at_risk_list = [s for s in all_students_mapped if s["status"] in ["at_risk", "inactive", "not_started"]]
    at_risk_list.sort(key=lambda x: x["progress"])
    
    # Tutorial wise completion
    tut_completion_res = await db.execute(
        select(
            Tutorial.tutorial_number,
            func.count(UserTutorial.user_id).label("count")
        ).select_from(Tutorial)
        .join(UserTutorial, (UserTutorial.tutorial_id == Tutorial.id) & (UserTutorial.practiced == True))
        .join(User, (User.id == UserTutorial.user_id) & (User.role == "student") & (User.college_id == college_id))
        .filter(Tutorial.course_id == "linux")
        .group_by(Tutorial.tutorial_number)
    )
    tut_completion_data = tut_completion_res.all()
    tut_counts = {row.tutorial_number: row.count for row in tut_completion_data}
    
    tutorial_completion = []
    for i in range(1, total_tutorials + 1):
        count = tut_counts.get(i, 0)
        rate = round((count / total) * 100) if total > 0 else 0
        tutorial_completion.append({
            "number": i,
            "completedCount": count,
            "rate": rate
        })

    return {
        "totalStudents": total,
        "avgProgress": round(total_progress / total) if total > 0 else 0,
        "avgWatched": round(total_watched / total, 1) if total > 0 else 0,
        "totalTutorials": total_tutorials,
        "avgXP": round(total_xp / total) if total > 0 else 0,
        "totalXP": total_xp,
        "statusData": [
            {"name": "Completed", "value": status_counts["completed"], "color": "hsl(142, 76%, 36%)"},
            {"name": "Active", "value": status_counts["active"], "color": "hsl(221, 83%, 53%)"},
            {"name": "At Risk of Completion", "value": status_counts["at_risk"], "color": "hsl(38, 92%, 50%)"},
            {"name": "Inactive", "value": status_counts["inactive"], "color": "hsl(0, 72%, 51%)"}
        ],
        "progressData": [
            {"name": "0%", "value": progress_counts["0%"], "color": "hsl(0, 72%, 70%)"},
            {"name": "1–25%", "value": progress_counts["1–25%"], "color": "hsl(25, 95%, 60%)"},
            {"name": "26–50%", "value": progress_counts["26–50%"], "color": "hsl(38, 92%, 55%)"},
            {"name": "51–75%", "value": progress_counts["51–75%"], "color": "hsl(221, 83%, 60%)"},
            {"name": "76–99%", "value": progress_counts["76–99%"], "color": "hsl(142, 60%, 50%)"},
            {"name": "100%", "value": progress_counts["100%"], "color": "hsl(142, 76%, 36%)"}
        ],
        "tutorialCompletion": tutorial_completion,
        "topPerformers": top_performers,
        "atRisk": at_risk_list
    }


# ============================================================
# Coordinator Feedback Summary (College-scoped)
# ============================================================

@router.get("/colleges/{college_id}/feedback-summary")
async def get_coordinator_feedback_summary(
    college_id: str,
    tutorial_id: Optional[str] = Query(None, description="Filter by tutorial UUID"),
    step_type: Optional[str] = Query(None, description="Filter by step type"),
    reason: Optional[str] = Query(None, description="Filter by reason key"),
    user: User = Depends(require_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """
    Feedback analytics for a coordinator's college.
    Same shape as admin feedback-summary, but hard-filtered to the given college.
    Coordinators can only access their own college.
    """
    import uuid as uuid_mod

    # Enforce college access
    if user.role == "coordinator" and str(user.college_id) != str(college_id):
        raise HTTPException(
            status_code=403,
            detail="You can only view your own college's feedback",
        )

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

    # ----- Step 2: Build filtered query (always scoped to college) -----
    base_query = (
        select(TutorialFeedback)
        .options(selectinload(TutorialFeedback.user))
        .join(User, TutorialFeedback.user_id == User.id)
        .filter(User.college_id == college_id)
    )

    if tutorial_id:
        base_query = base_query.filter(TutorialFeedback.tutorial_id == uuid_mod.UUID(tutorial_id))
    if step_type:
        base_query = base_query.filter(TutorialFeedback.step_type == step_type)

    res_fb = await db.execute(base_query.order_by(TutorialFeedback.created_at.desc()))
    all_feedback = res_fb.scalars().all()

    # If reason filter is active, narrow down
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

    # ----- Step 4: College name -----
    res_col = await db.execute(select(College.name).filter(College.id == college_id))
    college_row = res_col.first()
    college_name = college_row.name if college_row else "Unknown"

    # ----- Step 5: Tutorial info lookup -----
    tutorial_ids = list({fb.tutorial_id for fb in all_feedback})
    if tutorial_ids:
        res_tuts = await db.execute(
            select(Tutorial.id, Tutorial.title, Tutorial.tutorial_number)
            .filter(Tutorial.id.in_(tutorial_ids))
        )
        tut_map = {t.id: {"title": t.title, "number": t.tutorial_number} for t in res_tuts.all()}
    else:
        tut_map = {}

    # ----- Step 6: Build entries grouped by tutorial -----
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
        parts = (student_user.display_name or "").split()
        initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"

        tutorial_groups[tid]["entries"].append({
            "id": str(fb.id),
            "studentId": str(fb.user_id),
            "studentName": student_user.display_name or student_user.username,
            "studentInitials": initials,
            "collegeName": college_name,
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

    # ----- Step 7: Unique affected students count -----
    unique_students = len({str(fb.user_id) for fb in all_feedback})

    # ----- Step 8: All distinct reason keys (from college-scoped feedback) -----
    res_college_fb = await db.execute(
        select(TutorialFeedback.reasons)
        .join(User, TutorialFeedback.user_id == User.id)
        .filter(User.college_id == college_id)
    )
    all_reason_lists = res_college_fb.scalars().all()
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
