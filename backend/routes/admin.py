# ============================================================
# Admin routes — platform-wide aggregations + feedback analytics
# ============================================================
# 1. /platform-summary  — Overview + Analytics tab data
# 2. /feedback-summary   — Aggregated student feedback
# 3. /students/{id}/feedback — Per-student feedback detail
# ============================================================

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, case

from database import get_db
from models import User, College, UserTutorial, Tutorial
from models.feedback import TutorialFeedback
from dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/platform-summary")
async def get_platform_summary(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a single, pre-computed payload for the admin Overview + Analytics tabs.
    Everything is done in SQL — no Python loops over students.
    """
    tot_tut_res = await db.execute(select(func.count(Tutorial.id)).filter(Tutorial.course_id == "linux"))
    total_tutorials = tot_tut_res.scalar() or 20

    # ----- Per-student metrics (one query) -----
    res_metrics = await db.execute(
        select(
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
    ).group_by(User.id)
    )
    student_metrics = res_metrics.all()

    # ----- Build college name lookup -----
    colleges_res = await db.execute(select(College.id, College.name))
    colleges = colleges_res.all()
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
    res_stats = await db.execute(
        select(
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
    )
    )
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
