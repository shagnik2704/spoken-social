# ============================================================
# Admin Routes — feedback analytics
# ============================================================

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from dependencies import require_admin
from models import User, Tutorial, College
from models.feedback import TutorialFeedback

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/feedback-summary")
def get_feedback_summary(
    college_id: Optional[str] = Query(None, description="Filter by college"),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated feedback data for the admin dashboard:
    1. Top reasons (across all feedback entries)
    2. Per-student feedback history (most recent first)
    """

    # ----- Base query -----
    base_query = db.query(TutorialFeedback).join(
        User, TutorialFeedback.user_id == User.id
    )

    if college_id:
        base_query = base_query.filter(User.college_id == college_id)

    all_feedback = base_query.order_by(TutorialFeedback.created_at.desc()).all()

    # ----- Aggregate reason counts -----
    reason_counts: dict[str, int] = {}
    step_type_counts: dict[str, int] = {}
    total_entries = len(all_feedback)

    for fb in all_feedback:
        # Count step types
        step_type_counts[fb.step_type] = step_type_counts.get(fb.step_type, 0) + 1

        # Count individual reasons
        for reason in (fb.reasons or []):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    # Sort reasons by frequency
    top_reasons = sorted(
        [{"key": k, "count": v, "percentage": round((v / total_entries) * 100) if total_entries > 0 else 0}
         for k, v in reason_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    # Sort step types by frequency
    step_breakdown = sorted(
        [{"stepType": k, "count": v} for k, v in step_type_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    # ----- Per-student feedback (grouped) -----
    # Get unique students who gave feedback
    students_with_feedback: dict[str, dict] = {}
    college_names: dict[str, str] = {}

    for fb in all_feedback:
        uid = str(fb.user_id)
        if uid not in students_with_feedback:
            student_user = fb.user
            # Cache college name
            cid = student_user.college_id
            if cid and cid not in college_names:
                college = db.query(College.name).filter_by(id=cid).first()
                college_names[cid] = college.name if college else cid

            parts = (student_user.display_name or "").split()
            initials = "".join(p[0].upper() for p in parts[:2]) if parts else "?"

            students_with_feedback[uid] = {
                "id": uid,
                "name": student_user.display_name or student_user.username,
                "initials": initials,
                "collegeName": college_names.get(cid, "Unknown") if cid else "Unknown",
                "feedbackCount": 0,
                "entries": [],
            }

        # Get tutorial title
        tutorial = db.query(Tutorial.title, Tutorial.tutorial_number).filter_by(
            id=fb.tutorial_id
        ).first()

        students_with_feedback[uid]["feedbackCount"] += 1
        students_with_feedback[uid]["entries"].append({
            "id": fb.id,
            "tutorialNumber": tutorial.tutorial_number if tutorial else 0,
            "tutorialTitle": tutorial.title if tutorial else "Unknown",
            "stepType": fb.step_type,
            "reasons": fb.reasons or [],
            "otherText": fb.other_text,
            "createdAt": fb.created_at.isoformat() if fb.created_at else None,
        })

    # Sort students by most feedback (most struggling first)
    students_list = sorted(
        students_with_feedback.values(),
        key=lambda s: s["feedbackCount"],
        reverse=True,
    )

    return {
        "totalEntries": total_entries,
        "topReasons": top_reasons,
        "stepBreakdown": step_breakdown,
        "students": students_list,
    }


@router.get("/students/{student_id}/feedback")
def get_student_feedback(
    student_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
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
    student = db.query(User).filter_by(id=sid).first()
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")

    # Get college name
    college_name = "Unknown"
    if student.college_id:
        college = db.query(College.name).filter_by(id=student.college_id).first()
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
    feedback_entries = (
        db.query(TutorialFeedback)
        .filter(TutorialFeedback.user_id == sid)
        .order_by(TutorialFeedback.created_at.desc())
        .all()
    )

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

    for fb in feedback_entries:
        tutorial = db.query(Tutorial.title, Tutorial.tutorial_number).filter_by(
            id=fb.tutorial_id
        ).first()

        entry = {
            "id": fb.id,
            "tutorialId": str(fb.tutorial_id),
            "tutorialNumber": tutorial.tutorial_number if tutorial else 0,
            "tutorialTitle": tutorial.title if tutorial else "Unknown",
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
