"""
Guardrail tests for the SQL aggregation behind /api/admin/platform-summary.

The endpoint used to load every student on the platform into Python and derive the
counters, progress buckets and top-10 lists there. Those derivations now happen in SQL,
so these pin the status ladder at its boundaries, the progress buckets, and the ordering
of the two lists — including the tiebreaker, which the Python version never had.
"""

import uuid

import pytest

from models.college import College
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.user import User
from services.jwt import create_access_token

pytestmark = pytest.mark.asyncio(loop_scope="session")

TUTORIAL_COUNT = 10          # so the "active" threshold is watched > int(10 * 0.3) == 3


def make_student(name):
    return User(
        id=uuid.uuid4(),
        username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org",
        display_name=name,
        role="student",
        college_id="c1",
    )


@pytest.fixture
async def cohort(db):
    """One student per status, with progress chosen to land in known buckets."""
    db.add_all([College(id="c1", name="College One"), Course(id="linux", title="Linux")])
    await db.flush()

    tuts = [
        Tutorial(id=uuid.uuid4(), course_id="linux", tutorial_number=i, title=f"T{i}")
        for i in range(1, TUTORIAL_COUNT + 1)
    ]
    db.add_all(tuts)

    admin = User(
        id=uuid.uuid4(), username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org", display_name="Admin", role="admin",
    )
    s_completed = make_student("Completed")
    s_active = make_student("Active")
    s_at_risk = make_student("AtRisk")
    s_inactive = make_student("Inactive")
    s_not_started = make_student("NotStarted")
    students = [s_completed, s_active, s_at_risk, s_inactive, s_not_started]
    db.add_all(students + [admin])
    await db.flush()

    db.add_all([UserCourse(user_id=s.id, course_id="linux") for s in students])

    # completed: all 10 practiced -> progress 100
    db.add_all([
        UserTutorial(user_id=s_completed.id, tutorial_id=t.id, watched=True, practiced=True, xp_earned=10)
        for t in tuts
    ])
    # active: 5 watched (> 3), 2 practiced -> progress 20
    db.add_all([
        UserTutorial(user_id=s_active.id, tutorial_id=tuts[i].id, watched=True,
                     practiced=(i < 2), xp_earned=5)
        for i in range(5)
    ])
    # at_risk: 2 watched (> 0 but <= 3), 1 practiced -> progress 10
    db.add_all([
        UserTutorial(user_id=s_at_risk.id, tutorial_id=tuts[i].id, watched=True,
                     practiced=(i < 1), xp_earned=5)
        for i in range(2)
    ])
    # inactive: nothing watched, but XP on the record -> progress 0
    db.add(UserTutorial(user_id=s_inactive.id, tutorial_id=tuts[0].id, watched=False,
                        practiced=False, xp_earned=5))
    # not_started: no UserTutorial rows at all
    await db.commit()

    token = create_access_token(str(admin.id), effective_role="admin")
    return {"headers": {"Authorization": f"Bearer {token}"}, "students": students}


async def _metrics(client, cohort):
    resp = await client.get("/api/admin/platform-summary?course_id=linux", headers=cohort["headers"])
    assert resp.status_code == 200
    return resp.json()


async def test_status_ladder_boundaries(client, cohort):
    data = await _metrics(client, cohort)
    m = data["metrics"]
    assert m["totalStudents"] == 5
    assert m["totalCompleted"] == 1
    assert m["totalActive"] == 1
    assert m["totalAtRisk"] == 1
    # totalInactive folds inactive + not_started, as it always has
    assert m["totalInactive"] == 2
    assert m["totalNotStarted"] == 1


async def test_progress_buckets(client, cohort):
    data = await _metrics(client, cohort)
    buckets = {b["name"]: b["value"] for b in data["progressDistribution"]}
    # inactive (0%) and not_started (0%) -> "0%"; at_risk (10%) and active (20%) -> "1–25%";
    # completed (100%) -> "100%"
    assert buckets["0%"] == 2
    assert buckets["1–25%"] == 2
    assert buckets["26–50%"] == 0
    assert buckets["51–75%"] == 0
    assert buckets["76–99%"] == 0
    assert buckets["100%"] == 1


async def test_averages_and_completion_rate(client, cohort):
    m = (await _metrics(client, cohort))["metrics"]
    # progress values are 100, 20, 10, 0, 0 -> mean 26
    assert m["avgProgress"] == 26
    assert m["completionRate"] == 20          # 1 of 5 completed
    assert m["avgXP"] == round((100 + 25 + 10 + 5) / 5)


async def test_top_performers_are_ordered_by_xp_desc(client, cohort):
    data = await _metrics(client, cohort)
    xps = [s["xp"] for s in data["topPerformers"]]
    assert xps == sorted(xps, reverse=True)
    assert all(x > 0 for x in xps), "students with no XP must not appear"
    assert data["topPerformers"][0]["name"] == "Completed"


async def test_at_risk_is_ordered_by_progress_asc(client, cohort):
    data = await _metrics(client, cohort)
    names = [s["name"] for s in data["atRiskStudents"]]
    progresses = [s["progress"] for s in data["atRiskStudents"]]
    assert progresses == sorted(progresses)
    assert set(names) == {"AtRisk", "Inactive", "NotStarted"}
    assert "Active" not in names and "Completed" not in names


async def test_list_order_is_deterministic_across_calls(client, cohort):
    """The Python version sorted an unordered result set, so ties had no defined order."""
    first = await _metrics(client, cohort)
    second = await _metrics(client, cohort)
    assert [s["id"] for s in first["topPerformers"]] == [s["id"] for s in second["topPerformers"]]
    assert [s["id"] for s in first["atRiskStudents"]] == [s["id"] for s in second["atRiskStudents"]]


async def test_student_shape_is_unchanged(client, cohort):
    student = (await _metrics(client, cohort))["topPerformers"][0]
    assert set(student) == {
        "id", "name", "initials", "xp", "progress", "status",
        "watched", "completed", "minitasksOpted", "collegeName",
    }
    assert student["collegeName"] == "College One"
    assert student["initials"] == "C"
