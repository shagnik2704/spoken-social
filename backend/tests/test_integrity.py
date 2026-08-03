"""Tests for the XP integrity checker.

The checker exists because ~49k XP of unpaid work sat undetected for four
months. So the tests that matter most reconstruct the exact production shapes
from that audit and assert the checker catches them — a checker that only
reports zeros on clean data would be worthless.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from models.course import Course
from models.tutorial import Tutorial, UserTutorial
from models.user import User
from services.integrity import check_xp_integrity, find_drifted_users

pytestmark = pytest.mark.asyncio(loop_scope="session")


def make_user(xp, *, name="Student", role="student", level=1):
    return User(
        id=uuid.uuid4(),
        username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org",
        display_name=name,
        role=role,
        is_test_account=False,
        level=level,
        xp_total=xp,
    )


async def setup_course(db):
    db.add(Course(id="linux", title="Linux"))
    tutorials = [
        Tutorial(id=uuid.uuid4(), course_id="linux", tutorial_number=n, title=f"T{n}")
        for n in range(1, 4)
    ]
    db.add_all(tutorials)
    await db.commit()
    return tutorials


async def progress(db, user, tutorial, *, xp_earned, **flags):
    db.add(UserTutorial(
        user_id=user.id, tutorial_id=tutorial.id, xp_earned=xp_earned, **flags
    ))
    await db.commit()


async def test_clean_system_is_healthy(db):
    tutorials = await setup_course(db)
    user = make_user(25, level=1)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=25,
                   watched=True, practiced=True, assignment_done=True)

    result = await check_xp_integrity(db)

    assert result["healthy"] is True
    assert all(v == 0 for k, v in result.items() if k != "healthy")


async def test_detects_the_unpaid_forum_shape(db):
    """The dominant production defect: both forum flags set but xp_earned
    counting only the three non-forum steps — 2,929 rows looked like this."""
    tutorials = await setup_course(db)
    user = make_user(25)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=25,
                   watched=True, practiced=True, assignment_done=True,
                   forum_asked=True, forum_answered=True)

    result = await check_xp_integrity(db)

    assert result["healthy"] is False
    assert result["tutorial_rows_off"] == 1
    assert result["xp_drift"] == 15


async def test_detects_total_below_its_own_rows(db):
    """The second defect: 37 students whose xp_total sat below the sum of their
    stored rows, so three ledgers gave three answers."""
    tutorials = await setup_course(db)
    user = make_user(10)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=25,
                   watched=True, practiced=True, assignment_done=True)

    result = await check_xp_integrity(db)

    assert result["user_totals_off"] == 1
    assert result["xp_drift"] == 15


async def test_detects_stale_level(db):
    await setup_course(db)
    user = make_user(800, level=1)
    db.add(user)
    await db.commit()

    result = await check_xp_integrity(db)

    assert result["levels_off"] == 1


async def test_detects_unachievable_total(db):
    """No sequence of awards produces 27 — every award is a multiple of 5."""
    await setup_course(db)
    db.add(make_user(27, level=1))
    await db.commit()

    result = await check_xp_integrity(db)

    assert result["impossible_totals"] == 1


async def test_detects_row_above_the_maximum(db):
    tutorials = await setup_course(db)
    user = make_user(0)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=999)

    result = await check_xp_integrity(db)

    assert result["impossible_rows"] == 1


async def test_detects_null_test_account_flags(db):
    """The NULL that hid 2,441 students. The column is NOT NULL now, so this
    should stay zero — but the check is what would notice if a migration ever
    relaxed it again."""
    await setup_course(db)
    db.add(make_user(0))
    await db.commit()

    result = await check_xp_integrity(db)

    assert result["null_test_flags"] == 0


async def test_non_students_are_not_flagged(db):
    """Admins can hold manually granted XP with no tutorial rows behind it."""
    await setup_course(db)
    db.add(make_user(50, name="Admin", role="admin", level=1))
    await db.commit()

    result = await check_xp_integrity(db)

    assert result["healthy"] is True


async def test_drift_is_signed_toward_students(db):
    """Positive drift means students are owed; negative means over-credited."""
    tutorials = await setup_course(db)
    owed, over = make_user(0), make_user(40)
    db.add_all([owed, over])
    await db.commit()
    await progress(db, owed, tutorials[0], xp_earned=0, watched=True)
    await progress(db, over, tutorials[1], xp_earned=40, watched=True)

    result = await check_xp_integrity(db)

    assert result["xp_drift"] == (10 - 0) + (10 - 40)


async def test_find_drifted_users_names_the_worst_first(db):
    tutorials = await setup_course(db)
    small, large = make_user(0, name="Small"), make_user(0, name="Large")
    db.add_all([small, large])
    await db.commit()
    await progress(db, small, tutorials[0], xp_earned=0, watched=True)
    await progress(db, large, tutorials[1], xp_earned=0,
                   watched=True, practiced=True, assignment_done=True,
                   forum_asked=True, forum_answered=True)

    drifted = await find_drifted_users(db)

    assert [d["name"] for d in drifted] == ["Large", "Small"]
    assert drifted[0]["drift"] == 40
    assert drifted[0]["implied"] == 40


async def test_find_drifted_users_is_empty_when_clean(db):
    tutorials = await setup_course(db)
    user = make_user(10)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=10, watched=True)

    assert await find_drifted_users(db) == []


# ── the forum verification window ────────────────────────────────────────────
# Forum XP is held until a post survives VERIFICATION_HOURS, so the radio is set
# while xp_earned still excludes it. The checker must treat that as fine while
# the post is inside its window, and as a violation once it isn't.

async def pending_post(db, user, tutorial, *, hours_ago, activity_type="question", awarded=False, deleted=False):
    from models.forum_activity import ForumActivity

    db.add(ForumActivity(
        user_id=user.id, tutorial_id=tutorial.id, forum_post_id=uuid.uuid4().int % 10**8,
        activity_type=activity_type,
        posted_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        synced_at=datetime.now(timezone.utc),
        xp_awarded=awarded, xp_amount=0,
    ))
    await db.commit()


async def test_post_inside_its_window_is_not_a_violation(db):
    """The radio is on, the XP is not yet paid — correct, not drift."""
    tutorials = await setup_course(db)
    user = make_user(10)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=10, watched=True, forum_asked=True)
    await pending_post(db, user, tutorials[0], hours_ago=1)

    result = await check_xp_integrity(db)

    assert result["healthy"] is True
    assert result["xp_drift"] == 0


async def test_post_past_its_window_is_a_violation(db):
    """Same row, older post: the worker should have paid it by now, so a stalled
    sweep surfaces here instead of staying invisible."""
    tutorials = await setup_course(db)
    user = make_user(10)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=10, watched=True, forum_asked=True)
    await pending_post(db, user, tutorials[0], hours_ago=30)

    result = await check_xp_integrity(db)

    assert result["healthy"] is False
    assert result["tutorial_rows_off"] == 1
    assert result["xp_drift"] == 5


async def test_deleted_pending_post_does_not_excuse_the_gap(db):
    """A deleted post must not keep exempting a radio that is still set —
    process_forum_delete clears the radio, so this state means something went
    wrong."""
    tutorials = await setup_course(db)
    user = make_user(10)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=10, watched=True, forum_asked=True)
    await pending_post(db, user, tutorials[0], hours_ago=1, deleted=True)
    from sqlalchemy import text
    await db.execute(text("UPDATE forum_activities SET deleted_on_forum = true"))
    await db.commit()

    result = await check_xp_integrity(db)

    assert result["healthy"] is False


async def test_awarded_post_no_longer_exempts(db):
    """Once paid, the row must match exactly — the exemption cannot linger."""
    tutorials = await setup_course(db)
    user = make_user(15)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=15, watched=True, forum_asked=True)
    await pending_post(db, user, tutorials[0], hours_ago=1, awarded=True)

    result = await check_xp_integrity(db)

    assert result["healthy"] is True


async def test_exemption_is_typed_not_blanket(db):
    """A pending question excuses 5 XP, not the 10 owed for an answer."""
    tutorials = await setup_course(db)
    user = make_user(10)
    db.add(user)
    await db.commit()
    await progress(db, user, tutorials[0], xp_earned=10, watched=True,
                   forum_asked=True, forum_answered=True)
    await pending_post(db, user, tutorials[0], hours_ago=1, activity_type="question")

    result = await check_xp_integrity(db)

    assert result["healthy"] is False
    assert result["xp_drift"] == 10


async def test_window_matches_the_workers_sweep(db):
    """The exemption window and the sweep threshold come from one constant, so
    they cannot drift into a gap where XP is neither paid nor flagged."""
    from services.forum import VERIFICATION_HOURS
    from services.integrity import PENDING_FORUM_XP

    assert f"{VERIFICATION_HOURS} hours" in PENDING_FORUM_XP


async def test_expressions_track_the_real_xp_rules(db):
    """Built from XP_MAP, not hardcoded — changing the earning rules must not
    leave the checker asserting the old ones."""
    from services.integrity import FLAG_SUM, MAX_TUTORIAL_XP, XP_STEP
    from services.xp import XP_MAP

    assert MAX_TUTORIAL_XP == sum(XP_MAP.values())
    assert XP_STEP == min(XP_MAP.values())
    for column in XP_MAP:
        assert column in FLAG_SUM
