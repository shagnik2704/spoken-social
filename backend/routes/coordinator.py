# ============================================================
# Coordinator & Admin routes — optimized with SQL aggregations
# ============================================================
# - All queries use SQL aggregations (no Python loops over students)
# - Student listing is paginated (default 50 per page)
# - Role-based access: coordinator sees own college, admin sees all
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, literal

from database import get_db
from models import User, College, UserCourse, UserTutorial, Tutorial
from dependencies import get_current_user, require_coordinator, require_admin

router = APIRouter(prefix="/api/coordinator", tags=["coordinator"])


# ===== HELPER: Build aggregated college summary from DB =====

def _college_summary_query(db: Session, college_filter=None):
    """
    Returns a list of college summary dicts with metrics computed in SQL.
    If college_filter is provided, only returns that college.
    """
    # Count total tutorials for the linux course (used for progress calc)
    total_tutorials = db.query(func.count(Tutorial.id)).filter(
        Tutorial.course_id == "linux"
    ).scalar() or 20  # fallback

    # Base query: join users → user_tutorials → tutorials
    # Aggregate per college
    q = db.query(
        College.id,
        College.name,
        College.location,
        College.coordinator_name,
        College.course_id,
        func.count(User.id).label("total_students"),
        # Count by activity: watched > 50% = active, watched == total = completed, etc.
        func.count(func.nullif(
            case(
                (func.coalesce(
                    db.query(func.count(UserTutorial.tutorial_id)).filter(
                        UserTutorial.user_id == User.id,
                        UserTutorial.watched == True,
                    ).correlate(User).scalar_subquery(), 0
                ) == total_tutorials, "completed"),
                else_=None
            ), None
        )).label("completed_count"),
        func.avg(User.xp_total).label("avg_xp"),
    ).join(User, User.college_id == College.id)

    if college_filter:
        q = q.filter(College.id == college_filter)

    q = q.group_by(College.id)
    return q.all()


def _build_college_summary(db: Session, college_id: str | None = None) -> list[dict]:
    """
    Builds college summaries using individual SQL queries per college.
    This approach is clearer and avoids complex correlated subqueries.
    """
    if college_id:
        colleges = db.query(College).filter(College.id == college_id).all()
    else:
        colleges = db.query(College).all()

    total_tutorials = db.query(func.count(Tutorial.id)).filter(
        Tutorial.course_id == "linux"
    ).scalar() or 20

    summaries = []
    for college in colleges:
        # Get all student IDs for this college
        student_ids = db.query(User.id).filter(User.college_id == college.id).all()
        student_ids = [sid[0] for sid in student_ids]
        total = len(student_ids)

        if total == 0:
            summaries.append({
                "id": college.id,
                "name": college.name,
                "location": college.location or "",
                "coordinatorName": college.coordinator_name or "",
                "course": college.course_id or "linux",
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
        student_metrics = db.query(
            User.id,
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
            User.college_id == college.id
        ).group_by(User.id).all()

        num_completed = 0
        num_active = 0
        num_at_risk = 0
        num_inactive = 0
        total_progress = 0

        for row in student_metrics:
            uid, xp, watched_count, completed_count = row
            progress = round((completed_count / total_tutorials) * 100) if total_tutorials > 0 else 0
            total_progress += progress

            if completed_count >= total_tutorials:
                num_completed += 1
            elif watched_count > total_tutorials * 0.3:
                num_active += 1
            elif watched_count > 0:
                num_at_risk += 1
            else:
                num_inactive += 1

        avg_xp_val = db.query(func.avg(User.xp_total)).filter(
            User.college_id == college.id
        ).scalar() or 0

        summaries.append({
            "id": college.id,
            "name": college.name,
            "location": college.location or "",
            "coordinatorName": college.coordinator_name or "",
            "course": college.course_id or "linux",
            "totalStudents": total,
            "activeStudents": num_active + num_completed,
            "inactiveStudents": num_inactive,
            "atRiskStudents": num_at_risk,
            "completedStudents": num_completed,
            "avgProgress": round(total_progress / total) if total > 0 else 0,
            "avgXP": round(float(avg_xp_val)),
            "completionRate": round((num_completed / total) * 100) if total > 0 else 0,
        })

    return summaries


def _get_student_rows(db: Session, college_id: str, course_id: str = "linux",
                      page: int = 1, limit: int = 50,
                      sort: str = "progress", status_filter: str = "all",
                      search: str = ""):
    """
    Returns paginated student rows for a specific college.
    Sort and filter are done in SQL, not Python.
    """
    total_tutorials = db.query(func.count(Tutorial.id)).filter(
        Tutorial.course_id == course_id
    ).scalar() or 20

    # Build base query with tutorial aggregations
    watched_sub = func.count(
        case((UserTutorial.watched == True, UserTutorial.tutorial_id), else_=None)
    ).label("tutorials_watched")

    completed_sub = func.count(
        case((UserTutorial.practiced == True, UserTutorial.tutorial_id), else_=None)
    ).label("tutorials_completed")

    q = db.query(
        User.id,
        User.display_name,
        User.username,
        User.xp_total,
        watched_sub,
        completed_sub,
    ).outerjoin(
        UserTutorial, UserTutorial.user_id == User.id
    ).outerjoin(
        Tutorial,
        (Tutorial.id == UserTutorial.tutorial_id) & (Tutorial.course_id == course_id)
    ).filter(
        User.college_id == college_id,
        User.role == "student",
    ).group_by(User.id)

    # Search
    if search:
        q = q.filter(
            User.display_name.ilike(f"%{search}%") |
            User.username.ilike(f"%{search}%")
        )

    # We need to get all rows first to compute status (it depends on watched/completed counts)
    all_rows = q.all()

    # Compute progress + status for each
    students = []
    for row in all_rows:
        uid, name, username, xp, watched, completed = row
        progress = round((completed / total_tutorials) * 100) if total_tutorials > 0 else 0

        if completed >= total_tutorials:
            status = "completed"
        elif watched > total_tutorials * 0.3:
            status = "active"
        elif watched > 0:
            status = "at_risk"
        else:
            status = "inactive" if xp > 0 else "not_started"

        # Apply status filter
        if status_filter != "all":
            if status_filter == "inactive" and status not in ("inactive", "not_started"):
                continue
            elif status_filter != "inactive" and status != status_filter:
                continue

        # Build initials
        parts = (name or "").split()
        initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"

        students.append({
            "id": str(uid),
            "name": name or username or "",
            "initials": initials,
            "rollNo": "",  # Not in DB yet — placeholder
            "tutorialsWatched": watched,
            "tutorialsCompleted": completed,
            "totalTutorials": total_tutorials,
            "progress": progress,
            "xp": xp,
            "lastActive": "—",  # Not tracked yet — placeholder
            "status": status,
        })

    # Sort
    if sort == "progress":
        students.sort(key=lambda s: s["progress"], reverse=True)
    elif sort == "xp":
        students.sort(key=lambda s: s["xp"], reverse=True)
    elif sort == "name":
        students.sort(key=lambda s: s["name"])

    # Paginate
    total_count = len(students)
    total_pages = max(1, (total_count + limit - 1) // limit)
    start = (page - 1) * limit
    end = start + limit

    return {
        "students": students[start:end],
        "pagination": {
            "currentPage": page,
            "totalPages": total_pages,
            "totalRecords": total_count,
            "limit": limit,
        }
    }


# ===== ROUTES =====


@router.get("/colleges")
def get_all_colleges(
    user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """
    Returns all colleges with computed metrics.
    Coordinator and Admin both have access.
    """
    return _build_college_summary(db)


@router.get("/colleges/{college_id}")
def get_college_details(
    college_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("progress"),
    status: str = Query("all"),
    search: str = Query(""),
    user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """
    Returns a specific college's details + paginated student list.
    Coordinator can only access their own college; admin can access any.
    """
    # Coordinator can only see their own college
    if user.role == "coordinator" and user.college_id != college_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own college's students",
        )

    college = db.query(College).filter(College.id == college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    summary = _build_college_summary(db, college_id=college_id)
    if not summary:
        raise HTTPException(status_code=404, detail="College not found")

    student_data = _get_student_rows(
        db, college_id,
        page=page, limit=limit, sort=sort,
        status_filter=status, search=search,
    )

    return {
        "college": {
            "id": college.id,
            "name": college.name,
            "location": college.location or "",
            "coordinatorName": college.coordinator_name or "",
            "course": college.course_id or "linux",
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
