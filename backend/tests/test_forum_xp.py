"""Tests for forum XP and its verification window.

The rule these lock down is a product decision, not an implementation detail:
a forum post earns nothing until it has survived VERIFICATION_HOURS, so points
cannot be farmed by posting and deleting. The dashboard radio still flips
immediately so the student sees their post reflected.

Holding also fails safe. Awarding on arrival would mean XP is only clawed back
if a delete event is successfully delivered; holding needs only the absence of
one.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from models.course import Course
from models.forum_activity import ForumActivity
from models.tutorial import Tutorial, UserTutorial
from models.user import User
from services.forum import (
    VERIFICATION_HOURS,
    _award_forum_xp,
    process_forum_delete,
    process_forum_event,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

EMAIL = "learner@example.org"


async def setup(db, *, watched_xp=10):
    """A student partway through one tutorial of a course the forum knows about."""
    db.add(Course(id="linux", title="Linux", forum_category="Linux New"))
    tutorial = Tutorial(
        id=uuid.uuid4(), course_id="linux", tutorial_number=1,
        title="Basic Commands in Linux",
    )
    user = User(
        id=uuid.uuid4(), username=f"@{uuid.uuid4().hex[:8]}", email=EMAIL,
        display_name="Learner", role="student", is_test_account=False,
        level=1, xp_total=watched_xp,
    )
    db.add_all([tutorial, user])
    await db.flush()
    db.add(UserTutorial(
        user_id=user.id, tutorial_id=tutorial.id, watched=True, xp_earned=watched_xp,
    ))
    await db.commit()
    return user, tutorial


async def post(db, *, post_id=101, activity_type="question", tutorial_name="Basic-Commands-in-Linux"):
    result = await process_forum_event(
        db, forum_post_id=post_id, activity_type=activity_type, user_email=EMAIL,
        category="Linux New", tutorial_name=tutorial_name,
    )
    await db.commit()
    return result


async def state(db, user, tutorial):
    ut = (await db.execute(
        select(UserTutorial).filter_by(user_id=user.id, tutorial_id=tutorial.id)
    )).scalars().first()
    u = (await db.execute(select(User).filter_by(id=user.id))).scalars().first()
    return ut, u


async def age_activity(db, hours):
    """Backdate every activity so the sweep considers it verified."""
    acts = (await db.execute(select(ForumActivity))).scalars().all()
    for a in acts:
        a.posted_at = datetime.now(timezone.utc) - timedelta(hours=hours)
    await db.commit()


async def run_sweep(db):
    """The worker's award step, against activities past the window."""
    threshold = datetime.now(timezone.utc) - timedelta(hours=VERIFICATION_HOURS)
    acts = (await db.execute(select(ForumActivity).filter(
        ForumActivity.xp_awarded == False,  # noqa: E712
        ForumActivity.deleted_on_forum == False,  # noqa: E712
        ForumActivity.posted_at <= threshold,
        ForumActivity.tutorial_id.isnot(None),
    ))).scalars().all()
    for a in acts:
        user = (await db.execute(select(User).filter_by(id=a.user_id))).scalars().first()
        await _award_forum_xp(
            db, user, a.tutorial_id, a.activity_type,
            5 if a.activity_type == "question" else 10, a.forum_post_id,
        )
        a.xp_awarded = True
    await db.commit()
    return len(acts)


async def test_posting_flips_the_radio_but_pays_nothing(db):
    user, tutorial = await setup(db)

    result = await post(db)
    ut, u = await state(db, user, tutorial)

    assert result["status"] == "pending_verification"
    assert result["xp_awarded"] is False
    assert ut.forum_asked is True
    assert ut.xp_earned == 10
    assert u.xp_total == 10


async def test_sweep_pays_once_the_post_survives(db):
    user, tutorial = await setup(db)
    await post(db)
    await age_activity(db, VERIFICATION_HOURS + 1)

    awarded = await run_sweep(db)
    ut, u = await state(db, user, tutorial)

    assert awarded == 1
    assert ut.xp_earned == 15
    assert u.xp_total == 15


async def test_sweep_ignores_a_post_still_inside_its_window(db):
    user, tutorial = await setup(db)
    await post(db)

    awarded = await run_sweep(db)
    ut, _ = await state(db, user, tutorial)

    assert awarded == 0
    assert ut.xp_earned == 10


async def test_delete_inside_the_window_earns_nothing_ever(db):
    """The rule's whole purpose: post, delete, and you keep nothing — including
    the radio, which must not advertise a post that no longer exists."""
    user, tutorial = await setup(db)
    await post(db)

    await process_forum_delete(db, forum_post_id=101, activity_type="question")
    await db.commit()
    await age_activity(db, VERIFICATION_HOURS + 1)
    awarded = await run_sweep(db)
    ut, u = await state(db, user, tutorial)

    assert awarded == 0
    assert ut.forum_asked is False
    assert ut.xp_earned == 10
    assert u.xp_total == 10


async def test_delete_after_award_revokes(db):
    user, tutorial = await setup(db)
    await post(db)
    await age_activity(db, VERIFICATION_HOURS + 1)
    await run_sweep(db)

    await process_forum_delete(db, forum_post_id=101, activity_type="question")
    await db.commit()
    ut, u = await state(db, user, tutorial)

    assert ut.forum_asked is False
    assert ut.xp_earned == 10
    assert u.xp_total == 10


async def test_duplicate_webhook_is_idempotent(db):
    user, tutorial = await setup(db)
    await post(db)

    again = await post(db)
    activities = (await db.execute(select(ForumActivity))).scalars().all()

    assert again["status"] == "skipped"
    assert len(activities) == 1


async def test_sweep_pays_each_post_once(db):
    user, tutorial = await setup(db)
    await post(db)
    await age_activity(db, VERIFICATION_HOURS + 1)

    await run_sweep(db)
    second = await run_sweep(db)
    ut, u = await state(db, user, tutorial)

    assert second == 0
    assert ut.xp_earned == 15
    assert u.xp_total == 15


async def test_question_and_answer_are_scored_separately(db):
    user, tutorial = await setup(db)
    await post(db, post_id=101, activity_type="question")
    await post(db, post_id=102, activity_type="answer")
    await age_activity(db, VERIFICATION_HOURS + 1)

    await run_sweep(db)
    ut, u = await state(db, user, tutorial)

    assert ut.forum_asked is True and ut.forum_answered is True
    assert ut.xp_earned == 25
    assert u.xp_total == 25


async def test_unmapped_post_is_recorded_but_never_scored(db):
    """No matching tutorial means no row to attribute XP against. It must not
    crash, and the sweep must keep skipping it."""
    user, tutorial = await setup(db)

    result = await post(db, tutorial_name="A Tutorial That Does Not Exist")
    await age_activity(db, VERIFICATION_HOURS + 1)
    awarded = await run_sweep(db)
    activity = (await db.execute(select(ForumActivity))).scalars().first()
    ut, _ = await state(db, user, tutorial)

    assert result["status"] == "pending_verification"
    assert activity.tutorial_id is None
    assert awarded == 0
    assert ut.xp_earned == 10


# ── category matching ────────────────────────────────────────────────────────
# The forum has sent this course's category as both "Linux" and "Linux-New",
# and the codebase wrote it as "Linux New". Comparing raw strings meant only one
# spelling resolved and the rest fell through to a title-only match, which is
# safe only while titles stay unique across courses.

@pytest.mark.parametrize("sent", ["Linux-New", "Linux New", "linux-new", "  LINUX   NEW  "])
async def test_category_spellings_all_resolve(db, sent):
    from services.forum import find_course_by_forum_category

    db.add(Course(id="linux", title="Linux", forum_category="Linux-New"))
    await db.commit()

    course = await find_course_by_forum_category(db, sent)

    assert course is not None and course.id == "linux"


async def test_a_different_category_does_not_resolve(db):
    """Normalising must not blur distinct categories together."""
    from services.forum import find_course_by_forum_category

    db.add_all([
        Course(id="linux", title="Linux", forum_category="Linux-New"),
        Course(id="python", title="Python", forum_category="Python"),
    ])
    await db.commit()

    assert await find_course_by_forum_category(db, "Scilab") is None
    assert (await find_course_by_forum_category(db, "Python")).id == "python"


@pytest.mark.parametrize("configured", ["", "   ", "-"])
async def test_empty_category_matches_nothing(db, configured):
    """Production has received events with an empty category. Normalising both
    sides makes empty equal empty, so without an explicit guard such an event
    would bind to any course left with a blank category."""
    from services.forum import find_course_by_forum_category

    db.add(Course(id="linux", title="Linux", forum_category=configured))
    await db.commit()

    assert await find_course_by_forum_category(db, "") is None
    assert await find_course_by_forum_category(db, None) is None


async def test_post_resolves_to_the_right_course_via_category(db):
    """A title that exists in two courses must land in the one the category
    names — the case the title-only fallback would get wrong."""
    user, tutorial = await setup(db)
    db.add(Course(id="python", title="Python", forum_category="Python"))
    await db.flush()
    decoy = Tutorial(
        id=uuid.uuid4(), course_id="python", tutorial_number=1,
        title="Basic Commands in Linux",
    )
    db.add(decoy)
    await db.commit()

    await post(db)
    activity = (await db.execute(select(ForumActivity))).scalars().first()

    assert activity.tutorial_id == tutorial.id


async def test_unknown_email_is_ignored(db):
    await setup(db)

    result = await process_forum_event(
        db, forum_post_id=999, activity_type="question",
        user_email="nobody@example.org", category="Linux New",
        tutorial_name="Basic-Commands-in-Linux",
    )

    assert result["status"] == "ignored"
    assert (await db.execute(select(ForumActivity))).scalars().first() is None
