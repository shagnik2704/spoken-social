"""
Guardrail test for metrics.totalNotStarted on /api/admin/platform-summary.

Four FDP batches on production (python-fdp-9263, linux-fdp-9262, latex-fdp-9264,
scilab-fdp-9265 — 1591/1131/1037/809 students) have zero activity. In that state the
at-risk list came back empty, because has_any_activity excludes "not_started" students
from it, while the dashboard's badge read totalAtRisk + totalInactive — which counts every
one of them. So the panel showed "1591 need attention" above an empty list.

totalNotStarted lets the dashboard tell the two situations apart and say nobody has begun
rather than implying 1591 learners fell behind.
"""

import uuid

import pytest

from models.college import College
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.user import User
from services.jwt import create_access_token

pytestmark = pytest.mark.asyncio(loop_scope="session")


def make_student(college):
    return User(
        id=uuid.uuid4(),
        username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org",
        display_name="Student",
        role="student",
        college_id=college,
    )


@pytest.fixture
async def admin_headers(db):
    admin = User(
        id=uuid.uuid4(), username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org", display_name="Admin", role="admin",
    )
    db.add(admin)
    await db.commit()
    return {"Authorization": f"Bearer {create_access_token(str(admin.id), effective_role='admin')}"}


async def _summary(client, headers):
    resp = await client.get("/api/admin/platform-summary?course_id=linux", headers=headers)
    assert resp.status_code == 200
    return resp.json()


async def test_zero_activity_cohort_reports_everyone_as_not_started(client, db, admin_headers):
    """The FDP case: enrolled learners, none of whom has touched anything."""
    db.add_all([College(id="c1", name="College One"), Course(id="linux", title="Linux")])
    await db.flush()
    students = [make_student("c1") for _ in range(5)]
    db.add_all(students)
    await db.flush()
    db.add_all([UserCourse(user_id=s.id, course_id="linux") for s in students])
    await db.commit()

    data = await _summary(client, admin_headers)
    m = data["metrics"]

    assert m["totalStudents"] == 5
    assert m["totalNotStarted"] == 5, "every enrolled learner should count as not-started"
    assert m["totalAtRisk"] == 0
    # The dashboard keys its not-started state off this equality.
    assert m["totalNotStarted"] == m["totalStudents"]
    assert data["atRiskStudents"] == [], "nobody has started, so nobody is 'at risk' yet"


async def test_started_cohort_is_not_reported_as_not_started(client, db, admin_headers):
    """One learner with real activity is enough to leave the not-started state."""
    db.add_all([College(id="c2", name="College Two"), Course(id="linux", title="Linux")])
    await db.flush()
    tut = Tutorial(id=uuid.uuid4(), course_id="linux", tutorial_number=1, title="Intro")
    students = [make_student("c2") for _ in range(3)]
    db.add(tut)
    db.add_all(students)
    await db.flush()
    db.add_all([UserCourse(user_id=s.id, course_id="linux") for s in students])
    db.add(UserTutorial(user_id=students[0].id, tutorial_id=tut.id, watched=True, xp_earned=10))
    await db.commit()

    m = (await _summary(client, admin_headers))["metrics"]

    assert m["totalStudents"] == 3
    assert m["totalNotStarted"] == 2, "only the two untouched learners are not-started"
    assert m["totalNotStarted"] != m["totalStudents"], "cohort has begun; not the not-started state"
