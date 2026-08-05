"""
Guardrail tests for /api/admin/college-daily-xp.

The endpoint's docstring always claimed it averaged "across students", but the SQL used
AVG over a subquery that only emitted rows for students who earned XP that day — so the
denominator was earners, not enrolled. One active student out of 300 charted identically
to 300 out of 300, which made the per-college lines incomparable.

test_average_divides_by_enrolled_not_earners pins the corrected denominator.
"""

import uuid
from datetime import datetime, timezone

import pytest

from models.college import College
from models.course import Course, UserCourse
from models.user import User
from models.xp_event import XPEvent
from services.jwt import create_access_token

pytestmark = pytest.mark.asyncio(loop_scope="session")

MONTH = "2026-06"
# Mid-day UTC so the IST (+05:30) bucketing can't tip the event into an adjacent day.
EVENT_DAY = 15
EVENT_TS = datetime(2026, 6, EVENT_DAY, 6, 0, tzinfo=timezone.utc)


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
async def seeded(db):
    """One college, four enrolled students, exactly one of whom earns 100 XP."""
    db.add_all([College(id="c1", name="College One"), Course(id="linux", title="Linux")])
    await db.flush()

    students = [make_student("c1") for _ in range(4)]
    admin = User(
        id=uuid.uuid4(), username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org", display_name="Admin", role="admin",
    )
    db.add_all(students + [admin])
    await db.flush()

    db.add_all([UserCourse(user_id=s.id, course_id="linux") for s in students])
    db.add(XPEvent(
        user_id=students[0].id,
        source_type="tutorial_completion",
        source_id="t1",
        xp_delta=100,
        course_id="linux",
        created_at=EVENT_TS,
    ))
    await db.commit()

    token = create_access_token(str(admin.id), effective_role="admin")
    return {"headers": {"Authorization": f"Bearer {token}"}, "students": students}


async def test_average_divides_by_enrolled_not_earners(client, seeded):
    resp = await client.get(
        f"/api/admin/college-daily-xp?course_id=linux&month={MONTH}",
        headers=seeded["headers"],
    )
    assert resp.status_code == 200
    day = next(d for d in resp.json()["series"] if d["day"] == EVENT_DAY)

    # 100 XP over 4 enrolled students = 25.0. Averaging over earners would give 100.0.
    assert day["c1"] == 25.0, f"expected 100/4 enrolled, got {day['c1']}"


async def test_days_without_xp_are_zero(client, seeded):
    resp = await client.get(
        f"/api/admin/college-daily-xp?course_id=linux&month={MONTH}",
        headers=seeded["headers"],
    )
    series = resp.json()["series"]
    assert all(d["c1"] == 0 for d in series if d["day"] != EVENT_DAY)


async def test_untagged_events_are_excluded(client, seeded, db):
    """XP events predating course tagging carry a NULL course_id and must not be counted."""
    db.add(XPEvent(
        user_id=seeded["students"][1].id,
        source_type="tutorial_completion",
        source_id="t2",
        xp_delta=999,
        course_id=None,
        created_at=EVENT_TS,
    ))
    await db.commit()

    resp = await client.get(
        f"/api/admin/college-daily-xp?course_id=linux&month={MONTH}",
        headers=seeded["headers"],
    )
    day = next(d for d in resp.json()["series"] if d["day"] == EVENT_DAY)
    assert day["c1"] == 25.0, "an untagged event leaked into the course-scoped chart"
