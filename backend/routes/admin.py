# ============================================================
# Admin routes — platform-wide aggregations computed in SQL
# ============================================================
# One endpoint returns everything the Overview + Analytics tabs
# need: metrics, distributions, top performers, at-risk students,
# and tutorial-wise completion rates — all computed server-side.
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from database import get_db
from models import User, College, UserTutorial, Tutorial
from dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/platform-summary")
def get_platform_summary(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Returns a single, pre-computed payload for the admin Overview + Analytics tabs.
    Everything is done in SQL — no Python loops over students.
    """
    total_tutorials = db.query(func.count(Tutorial.id)).filter(
        Tutorial.course_id == "linux"
    ).scalar() or 20

    # ----- Per-student metrics (one query) -----
    student_metrics = db.query(
        User.id,
        User.display_name,
        User.username,
        User.xp_total,
        User.college_id,
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
        User.role == "student",
    ).group_by(User.id).all()

    # ----- Build college name lookup -----
    colleges = db.query(College.id, College.name).all()
    college_names = {c.id: c.name for c in colleges}

    # ----- Compute derived metrics -----
    students_enriched = []
    status_counts = {"completed": 0, "active": 0, "at_risk": 0, "inactive": 0, "not_started": 0}
    progress_buckets = {"0": 0, "1-25": 0, "26-50": 0, "51-75": 0, "76-99": 0, "100": 0}
    total_progress = 0

    for row in student_metrics:
        uid, name, username, xp, college_id, watched, completed = row
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
    tutorial_stats = db.query(
        Tutorial.tutorial_number,
        Tutorial.title,
        func.count(
            case((UserTutorial.practiced == True, UserTutorial.user_id), else_=None)
        ).label("completed_count"),
    ).outerjoin(
        UserTutorial, UserTutorial.tutorial_id == Tutorial.id
    ).filter(
        Tutorial.course_id == "linux",
    ).group_by(
        Tutorial.tutorial_number, Tutorial.title
    ).order_by(
        Tutorial.tutorial_number
    ).all()

    tutorial_completion = [
        {
            "number": t.tutorial_number,
            "name": t.title,
            "completedCount": t.completed_count,
            "rate": round((t.completed_count / total_students) * 100) if total_students > 0 else 0,
        }
        for t in tutorial_stats
    ]

    return {
        "metrics": {
            "totalStudents": total_students,
            "totalColleges": len(colleges),
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
            {"name": "At Risk", "value": status_counts["at_risk"], "color": "hsl(38, 92%, 50%)"},
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
