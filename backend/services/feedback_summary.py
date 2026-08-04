# ============================================================
# Feedback summary aggregation — shared by the admin and coordinator dashboards
# ============================================================
# The two callers used to carry independent copies of this. They had already drifted:
# coordinator's reason-dropdown query picked up a batch_id filter that admin's deliberately
# excludes (see the comment on _distinct_reason_keys below), so selecting a batch shrank the
# dropdown on one dashboard but not the other for no principled reason.
# ============================================================

import uuid as uuid_mod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dashboard_common import initials as build_initials
from models import College, Tutorial, User, UserCourse
from models.feedback import TutorialFeedback

STEP_TYPES = ["watched", "practiced", "assignmentDone", "forumAsked", "forumAnswered"]


def _base_query(course_id: str, college_id: Optional[str]):
    query = (
        select(TutorialFeedback)
        .options(selectinload(TutorialFeedback.user))
        .join(User, TutorialFeedback.user_id == User.id)
        .join(Tutorial, TutorialFeedback.tutorial_id == Tutorial.id)
        .filter(
            Tutorial.course_id == course_id,
            # Exclude test/placeholder accounts and non-students, like every other aggregate.
            User.role == "student",
            User.is_test_account != True,
        )
    )
    if college_id:
        query = query.filter(User.college_id == college_id)
    return query


async def _distinct_reason_keys(
    db: AsyncSession, course_id: str, college_id: Optional[str]
) -> list[str]:
    """
    All reason keys ever used in-scope, for the filter dropdown. Deliberately scoped to
    course + college only — NOT tutorial_id/step_type/batch_id/reason — so the dropdown's
    own options don't shift under the student as they narrow those filters.
    """
    query = (
        select(TutorialFeedback.reasons)
        .join(User, TutorialFeedback.user_id == User.id)
        .join(Tutorial, TutorialFeedback.tutorial_id == Tutorial.id)
        .filter(
            Tutorial.course_id == course_id,
            User.role == "student",
            User.is_test_account != True,
        )
    )
    if college_id:
        query = query.filter(User.college_id == college_id)

    rows = (await db.execute(query)).scalars().all()
    keys: set[str] = set()
    for reasons in rows:
        if reasons:
            keys.update(reasons)
    return sorted(keys)


async def build_feedback_summary(
    db: AsyncSession,
    *,
    course_id: str,
    college_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    tutorial_id: Optional[str] = None,
    step_type: Optional[str] = None,
    reason: Optional[str] = None,
) -> dict:
    """
    Filterable feedback analytics. `college_id=None` means platform-wide (the admin case);
    coordinator always passes its own college_id, which also scopes the reason dropdown to
    that college.
    """
    all_tutorials_res = await db.execute(
        select(Tutorial.id, Tutorial.title, Tutorial.tutorial_number)
        .filter(Tutorial.course_id == course_id)
        .order_by(Tutorial.tutorial_number)
    )
    all_tutorials = [
        {"id": str(t.id), "number": t.tutorial_number, "title": t.title}
        for t in all_tutorials_res.all()
    ]
    tut_map = {
        uuid_mod.UUID(t["id"]): {"title": t["title"], "number": t["number"]}
        for t in all_tutorials
    }

    query = _base_query(course_id, college_id)
    if batch_id:
        # Join the student's enrollment for THIS course. UserCourse PK is (user_id,
        # course_id), so this matches at most one row per feedback row — no fan-out.
        query = query.join(
            UserCourse,
            (UserCourse.user_id == TutorialFeedback.user_id) & (UserCourse.course_id == course_id),
        ).filter(UserCourse.batch_id == batch_id)
    if tutorial_id:
        query = query.filter(TutorialFeedback.tutorial_id == uuid_mod.UUID(tutorial_id))
    if step_type:
        query = query.filter(TutorialFeedback.step_type == step_type)
    if reason:
        # Postgres array containment (reasons @> ARRAY[reason]), not a Python post-filter.
        query = query.filter(TutorialFeedback.reasons.contains([reason]))

    all_feedback = (
        await db.execute(query.order_by(TutorialFeedback.created_at.desc()))
    ).scalars().all()
    total_entries = len(all_feedback)

    reason_counts: dict[str, int] = {}
    step_type_counts: dict[str, int] = {}
    for fb in all_feedback:
        step_type_counts[fb.step_type] = step_type_counts.get(fb.step_type, 0) + 1
        for r in (fb.reasons or []):
            reason_counts[r] = reason_counts.get(r, 0) + 1

    top_reasons = sorted(
        (
            {"key": k, "count": v, "percentage": round((v / total_entries) * 100) if total_entries > 0 else 0}
            for k, v in reason_counts.items()
        ),
        key=lambda x: x["count"],
        reverse=True,
    )
    step_breakdown = sorted(
        ({"stepType": k, "count": v} for k, v in step_type_counts.items()),
        key=lambda x: x["count"],
        reverse=True,
    )

    # College names for the entries. Derived from the returned rows rather than re-fetched
    # by id: for the coordinator's single-college case this is a one-entry dict with the same
    # result, and it costs nothing extra when there's no feedback to label.
    seen_college_ids = {fb.user.college_id for fb in all_feedback if fb.user.college_id}
    college_names: dict[str, str] = {}
    if seen_college_ids:
        rows = await db.execute(select(College.id, College.name).filter(College.id.in_(seen_college_ids)))
        college_names = {c.id: c.name for c in rows.all()}

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
        tutorial_groups[tid]["entries"].append({
            "id": str(fb.id),
            "studentId": str(fb.user_id),
            "studentName": student_user.display_name or student_user.username,
            "studentInitials": build_initials(student_user.display_name, student_user.username),
            "collegeName": college_names.get(cid, "Unknown") if cid else "Unknown",
            "stepType": fb.step_type,
            "reasons": fb.reasons or [],
            "otherText": fb.other_text,
            "createdAt": fb.created_at.isoformat() if fb.created_at else None,
        })
        tutorial_groups[tid]["_student_ids"].add(str(fb.user_id))

    for tg in tutorial_groups.values():
        tg["studentCount"] = len(tg["_student_ids"])
        del tg["_student_ids"]

    sorted_groups = sorted(tutorial_groups.values(), key=lambda g: len(g["entries"]), reverse=True)
    unique_students = len({str(fb.user_id) for fb in all_feedback})
    all_reason_keys = await _distinct_reason_keys(db, course_id, college_id)

    return {
        "filterOptions": {
            "tutorials": all_tutorials,
            "stepTypes": STEP_TYPES,
            "reasons": all_reason_keys,
        },
        "totalEntries": total_entries,
        "uniqueStudents": unique_students,
        "topReasons": top_reasons,
        "stepBreakdown": step_breakdown,
        "tutorialGroups": sorted_groups,
    }
