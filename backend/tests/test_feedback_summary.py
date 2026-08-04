"""
Guardrail tests for services.feedback_summary.build_feedback_summary, the function
routes/admin.py and routes/coordinator.py both now call instead of carrying their own
~120-line copy of this aggregation.

test_batch_filter_narrows_entries_but_not_the_reason_dropdown is the regression test for
the bug the unification fixed: coordinator's dropdown query used to join batch_id in
alongside college_id, so selecting a batch shrank the reason dropdown on the coordinator
feedback view but not on admin's. Both now share admin's documented behavior — the dropdown
tracks course + college only, so it stays stable while the volatile filters (tutorial,
step type, reason, batch) move.
"""

import uuid
from datetime import date, datetime, timezone

import pytest

from models.batch import Batch
from models.college import College
from models.course import Course, UserCourse
from models.feedback import TutorialFeedback
from models.tutorial import Tutorial
from models.user import User
from services.feedback_summary import build_feedback_summary

pytestmark = pytest.mark.asyncio(loop_scope="session")


def make_user(*, name="Student", role="student", test_account=False, college=None):
    return User(
        id=uuid.uuid4(),
        username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org",
        display_name=name,
        role=role,
        is_test_account=test_account,
        college_id=college,
    )


def make_feedback(*, user, tutorial, step_type, reasons):
    return TutorialFeedback(
        user_id=user.id,
        tutorial_id=tutorial.id,
        step_type=step_type,
        reasons=reasons,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def scenario(db):
    """
    Two colleges, one course, two tutorials, two batches. college_a has students in both
    batches so the batch filter has something to narrow; college_b exists so cross-college
    leakage is checkable.
    """
    college_a = College(id="college_a", name="College A")
    college_b = College(id="college_b", name="College B")
    course = Course(id="linux", title="Linux")
    db.add_all([college_a, college_b, course])
    await db.flush()

    batch1 = Batch(id="batch1", course_id="linux", name="Batch 1", start_date=date(2026, 1, 1), end_date=date(2026, 6, 1))
    batch2 = Batch(id="batch2", course_id="linux", name="Batch 2", start_date=date(2026, 1, 1), end_date=date(2026, 6, 1))
    tut1 = Tutorial(id=uuid.uuid4(), course_id="linux", tutorial_number=1, title="Intro")
    tut2 = Tutorial(id=uuid.uuid4(), course_id="linux", tutorial_number=2, title="Advanced")
    db.add_all([batch1, batch2, tut1, tut2])
    await db.flush()

    s1 = make_user(name="Student One", college="college_a")   # batch1, forumAsked/no_questions
    s2 = make_user(name="Student Two", college="college_a")   # batch2, forumAsked/difficult_to_use
    s3 = make_user(name="Student Three", college="college_b")  # batch1, watched/electricity
    coordinator = make_user(name="Coord", role="coordinator", college="college_a")
    test_student = make_user(name="Test Acct", test_account=True, college="college_a")
    db.add_all([s1, s2, s3, coordinator, test_student])
    await db.flush()

    db.add_all([
        UserCourse(user_id=s1.id, course_id="linux", batch_id="batch1"),
        UserCourse(user_id=s2.id, course_id="linux", batch_id="batch2"),
        UserCourse(user_id=s3.id, course_id="linux", batch_id="batch1"),
        UserCourse(user_id=coordinator.id, course_id="linux", batch_id="batch1"),
        UserCourse(user_id=test_student.id, course_id="linux", batch_id="batch1"),
    ])
    db.add_all([
        make_feedback(user=s1, tutorial=tut1, step_type="forumAsked", reasons=["no_questions"]),
        make_feedback(user=s2, tutorial=tut1, step_type="forumAsked", reasons=["difficult_to_use"]),
        make_feedback(user=s3, tutorial=tut2, step_type="watched", reasons=["electricity"]),
        make_feedback(user=coordinator, tutorial=tut1, step_type="forumAsked", reasons=["no_questions"]),
        make_feedback(user=test_student, tutorial=tut1, step_type="forumAsked", reasons=["no_questions"]),
    ])
    await db.commit()

    return {
        "college_a": college_a, "college_b": college_b,
        "s1": s1, "s2": s2, "s3": s3,
        "coordinator": coordinator, "test_student": test_student,
        "tut1": tut1, "tut2": tut2,
    }


async def test_admin_scope_includes_every_college(db, scenario):
    result = await build_feedback_summary(db, course_id="linux")
    assert result["totalEntries"] == 3
    seen_students = {e["studentId"] for g in result["tutorialGroups"] for e in g["entries"]}
    assert seen_students == {str(scenario["s1"].id), str(scenario["s2"].id), str(scenario["s3"].id)}


async def test_coordinator_scope_excludes_other_colleges(db, scenario):
    result = await build_feedback_summary(db, course_id="linux", college_id="college_a")
    assert result["totalEntries"] == 2
    seen_students = {e["studentId"] for g in result["tutorialGroups"] for e in g["entries"]}
    assert str(scenario["s3"].id) not in seen_students
    for g in result["tutorialGroups"]:
        for e in g["entries"]:
            assert e["collegeName"] == "College A"


async def test_test_accounts_and_non_students_are_excluded(db, scenario):
    result = await build_feedback_summary(db, course_id="linux", college_id="college_a")
    seen_students = {e["studentId"] for g in result["tutorialGroups"] for e in g["entries"]}
    # college_a has two real students (s1, s2) plus a coordinator and a test account, all
    # with feedback rows — only the two students should survive.
    assert seen_students == {str(scenario["s1"].id), str(scenario["s2"].id)}


async def test_batch_filter_narrows_entries_but_not_the_reason_dropdown(db, scenario):
    unfiltered = await build_feedback_summary(db, course_id="linux", college_id="college_a")
    filtered = await build_feedback_summary(db, course_id="linux", college_id="college_a", batch_id="batch1")

    assert unfiltered["totalEntries"] == 2
    assert filtered["totalEntries"] == 1  # only s1 is in batch1

    # The regression check: batch_id narrowed the entries but must not have narrowed the
    # dropdown. Before the fix, coordinator's dropdown query joined UserCourse and filtered
    # on batch_id too, so this would have dropped "difficult_to_use" (s2, batch2).
    assert unfiltered["filterOptions"]["reasons"] == ["difficult_to_use", "no_questions"]
    assert filtered["filterOptions"]["reasons"] == ["difficult_to_use", "no_questions"]


async def test_reason_dropdown_is_college_scoped_for_a_fixed_college(db, scenario):
    result = await build_feedback_summary(db, course_id="linux", college_id="college_a")
    assert "electricity" not in result["filterOptions"]["reasons"]  # that's college_b's reason

    admin_result = await build_feedback_summary(db, course_id="linux")
    assert "electricity" in admin_result["filterOptions"]["reasons"]


async def test_top_reasons_and_step_breakdown(db, scenario):
    result = await build_feedback_summary(db, course_id="linux")
    reason_keys = {r["key"]: r for r in result["topReasons"]}
    assert reason_keys["no_questions"]["count"] == 1
    assert reason_keys["electricity"]["count"] == 1
    step_keys = {s["stepType"]: s["count"] for s in result["stepBreakdown"]}
    assert step_keys == {"forumAsked": 2, "watched": 1}


async def test_tutorial_grouping_and_unique_student_count(db, scenario):
    result = await build_feedback_summary(db, course_id="linux", college_id="college_a")
    groups_by_tutorial = {g["tutorialTitle"]: g for g in result["tutorialGroups"]}
    assert groups_by_tutorial["Intro"]["studentCount"] == 2
    assert len(groups_by_tutorial["Intro"]["entries"]) == 2
    assert result["uniqueStudents"] == 2
