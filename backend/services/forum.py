# ============================================================
# Forum Sync Service — shared logic for processing forum events
# ============================================================
# This module is called by:
#   1. Webhook receiver (routes/webhooks.py) — records the post and
#      flips the dashboard radio, but does NOT award XP
#   2. Background worker (worker.py) — awards XP once a post has
#      survived the verification window
#
# XP is deliberately held back: a post that is created and then
# deleted within the window never earns anything, so points cannot
# be farmed by posting and removing. Holding also fails safe — it
# needs the absence of a delete event rather than the successful
# delivery of one.
#
# `process_forum_event` is idempotent: call it 100 times with the
# same forum_post_id and only one activity is recorded. Awarding and
# revoking both go through recompute_tutorial_xp (services/xp.py),
# so XP is always the sum of the flags rather than an accumulated
# counter.
# ============================================================

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User
from models.tutorial import Tutorial, UserTutorial
from models.course import Course
from models.forum_activity import ForumActivity
from models.xp_event import XPEvent

logger = logging.getLogger("spoken_social.forum_sync")

# XP values for forum activities
XP_FORUM_ASK = 5
XP_FORUM_ANS = 10

# How long a post must survive before its XP is awarded. Defined here and
# imported by the worker that enforces it and the integrity check that exempts
# it, so the two can never drift apart.
VERIFICATION_HOURS = 24


async def _sync_user_tutorial_forum_radios(
    db: AsyncSession,
    *,
    user_id,
    tutorial_id,
    activity_type: str,
) -> None:
    """Flip the dashboard forum radio as soon as a post is detected.

    XP deliberately does not follow yet — see process_forum_event. The flag and
    xp_earned therefore disagree for the length of the verification window, which
    services.integrity accounts for by subtracting still-pending forum XP before
    comparing. Once an activity ages past the window without being awarded, that
    exemption lapses and the invariant fires, so a stalled worker is visible.
    """
    if tutorial_id is None:
        return
    ut_result = await db.execute(
        select(UserTutorial).filter_by(user_id=user_id, tutorial_id=tutorial_id)
    )
    ut = ut_result.scalars().first()
    if not ut:
        return
    if activity_type == "question":
        ut.forum_asked = True
    elif activity_type == "answer":
        ut.forum_answered = True
    await db.flush()


async def find_user_by_forum_uid(db: AsyncSession, forum_user_id: int) -> User | None:
    """
    Look up a spoken-social user by their Spoken Tutorial forum user ID.
    Falls back to checking forum_activities for a previously linked user.

    NOTE: For this to work reliably, we need the forum webhook to include
    the user's email. For now, we store the forum_user_id mapping when we
    first encounter a user.
    """
    # For now, we cannot directly look up by forum_user_id since we don't
    # store it on the User model. The webhook should include the email.
    return None


async def find_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a spoken-social user by email."""
    result = await db.execute(select(User).filter_by(email=email))
    return result.scalars().first()


def normalize_forum_category(category: str | None) -> str:
    """Fold a forum category to a comparable form.

    The forum has sent this course's category as both "Linux" and "Linux-New",
    and the codebase has written it as "Linux New". Comparing raw strings meant
    only one spelling ever matched and the rest fell through to a title-only
    match. Hyphens, spacing and case are all treated as noise.
    """
    return " ".join((category or "").replace("-", " ").split()).lower()


async def find_course_by_forum_category(db: AsyncSession, category: str) -> Course | None:
    """The course a forum category belongs to, ignoring spelling differences."""
    wanted = normalize_forum_category(category)
    if not wanted:
        return None

    courses = (await db.execute(
        select(Course).filter(Course.forum_category.isnot(None))
    )).scalars().all()

    for course in courses:
        if normalize_forum_category(course.forum_category) == wanted:
            return course
    return None


async def find_tutorial_by_name(
    db: AsyncSession, category: str, tutorial_name: str
) -> Tutorial | None:
    """
    Find a Tutorial by matching the forum's tutorial name to our tutorial title.

    The forum uses names like 'Basic Commands in Linux' or 'Basic-Commands-in-Linux'.
    Our DB stores 'Basic Commands in Linux'. We normalize both to match.
    """
    # Normalize: replace hyphens with spaces for comparison
    normalized_name = tutorial_name.replace("-", " ")

    course = await find_course_by_forum_category(db, category)

    if not course:
        # Last resort: match the title across every course. Only safe while
        # titles are unique platform-wide — the moment two courses share one,
        # this silently attributes XP to whichever it finds first, so it is a
        # fallback rather than a strategy.
        logger.warning(
            "No course for forum category %r — falling back to a platform-wide "
            "title match for %r", category, tutorial_name,
        )
        tut_result = await db.execute(
            select(Tutorial).filter(Tutorial.title.ilike(normalized_name))
        )
        return tut_result.scalars().first()

    tut_result = await db.execute(
        select(Tutorial).filter(
            Tutorial.course_id == course.id,
            Tutorial.title.ilike(normalized_name),
        )
    )
    return tut_result.scalars().first()


async def process_forum_event(
    db: AsyncSession,
    *,
    forum_post_id: int,
    activity_type: str,  # "question" or "answer"
    user_email: str | None = None,
    user: User | None = None,
    category: str = "",
    tutorial_name: str = "",
    title: str | None = None,
    posted_at: datetime | None = None,
) -> dict:
    """
    Process a single forum event (question asked, answer posted, etc.)
    Idempotent — safe to call multiple times for the same forum_post_id.

    Returns a dict with processing result info.
    """

    # 1. Check if already processed (dedup by forum_post_id + activity_type)
    existing_result = await db.execute(
        select(ForumActivity).filter_by(
            forum_post_id=forum_post_id,
            activity_type=activity_type,
        )
    )
    existing = existing_result.scalars().first()
    if existing and not existing.deleted_on_forum:
        return {"status": "skipped", "reason": "already_processed"}

    # 2. Resolve the user
    if user is None and user_email:
        user = await find_user_by_email(db, user_email)
    if user is None:
        return {"status": "ignored", "reason": "user_not_found"}

    # 3. Resolve the tutorial
    tutorial = None
    tutorial_id = None
    if category and tutorial_name:
        tutorial = await find_tutorial_by_name(db, category, tutorial_name)
        if tutorial:
            tutorial_id = tutorial.id

    # 4. Determine XP
    xp_amount = XP_FORUM_ASK if activity_type == "question" else XP_FORUM_ANS

    # 5. If this was previously deleted and now re-created, update the existing row
    if existing and existing.deleted_on_forum:
        existing.deleted_on_forum = False
        existing.synced_at = datetime.now(timezone.utc)
        existing.posted_at = datetime.now(timezone.utc)
        existing.xp_awarded = False
        existing.xp_amount = 0
        await db.flush()
        await _sync_user_tutorial_forum_radios(
            db,
            user_id=user.id,
            tutorial_id=existing.tutorial_id,
            activity_type=activity_type,
        )
        return {"status": "restored", "forum_post_id": forum_post_id}

    # 6. Insert new ForumActivity row
    forum_url = f"https://forums.spoken-tutorial.org/question/{forum_post_id}/"

    activity = ForumActivity(
        user_id=user.id,
        tutorial_id=tutorial_id,
        forum_post_id=forum_post_id,
        activity_type=activity_type,
        title=title,
        category=category,
        tutorial_name=tutorial_name,
        forum_url=forum_url,
        posted_at=posted_at or datetime.now(timezone.utc),
        synced_at=datetime.now(timezone.utc),
        xp_awarded=False,
        xp_amount=0,
    )
    db.add(activity)
    await db.flush()

    # 7. No XP yet — the worker awards it once the post has survived the
    # verification window, so a post-and-delete cannot farm points. Only the
    # dashboard radio moves now, so the student sees their post reflected
    # immediately.
    await _sync_user_tutorial_forum_radios(
        db, user_id=user.id, tutorial_id=tutorial_id, activity_type=activity_type
    )

    await db.flush()
    return {
        "status": "pending_verification",
        "forum_post_id": forum_post_id,
        "xp_awarded": False,
        "xp_amount": 0,
    }


async def process_forum_delete(
    db: AsyncSession,
    *,
    forum_post_id: int,
    activity_type: str,
) -> dict:
    """
    Handle a deletion event from the forum.
    Revokes XP if it was previously awarded.
    """

    result = await db.execute(
        select(ForumActivity).filter_by(
            forum_post_id=forum_post_id,
            activity_type=activity_type,
        )
    )
    activity = result.scalars().first()

    if not activity:
        return {"status": "ignored", "reason": "not_tracked"}

    if activity.deleted_on_forum:
        return {"status": "skipped", "reason": "already_deleted"}

    activity.deleted_on_forum = True

    # Called whether or not XP was awarded. If the post was still inside its
    # verification window the radio is set but unpaid, so this only clears the
    # radio and recompute returns 0; if XP had been awarded, the same call takes
    # it back. Either way the row cannot be left claiming a deleted post.
    xp_delta = 0
    if activity.tutorial_id:
        xp_delta = await _revoke_forum_xp(
            db,
            user_id=activity.user_id,
            tutorial_id=activity.tutorial_id,
            activity_type=activity.activity_type,
            xp_amount=activity.xp_amount,
            forum_post_id=forum_post_id,
        )
    was_awarded, activity.xp_awarded = activity.xp_awarded, False

    await db.flush()
    return {
        "status": "deleted",
        "xp_revoked": activity.xp_amount if was_awarded else 0,
        "xp_delta": xp_delta,
        "user_id": str(activity.user_id),
    }


async def _award_forum_xp(
    db: AsyncSession,
    user: User,
    tutorial_id,
    activity_type: str,
    xp_amount: int,
    forum_post_id: int,
):
    """Award XP for a forum activity by setting the tutorial flag and recomputing
    xp_earned from flags (single source of truth — see services/xp.py). Forum XP counts
    once per tutorial per activity type; re-verifying the same activity is a no-op."""
    from services.xp import recompute_tutorial_xp, recalc_level

    ut_result = await db.execute(
        select(UserTutorial).filter_by(user_id=user.id, tutorial_id=tutorial_id)
    )
    ut = ut_result.scalars().first()
    if ut:
        if activity_type == "question":
            ut.forum_asked = True
        elif activity_type == "answer":
            ut.forum_answered = True
        xp_gained = recompute_tutorial_xp(ut)
    else:
        # No progress row to attribute against — credit global XP with the passed amount
        # so nothing is lost (course dashboards can't reflect it without a UserTutorial row).
        xp_gained = xp_amount

    if xp_gained != 0:
        user.xp_total += xp_gained
        recalc_level(user)
        course_id = (await db.execute(
            select(Tutorial.course_id).filter(Tutorial.id == tutorial_id)
        )).scalar()
        db.add(XPEvent(
            user_id=user.id,
            source_type="forum_activity",
            source_id=str(forum_post_id),
            xp_delta=xp_gained,
            course_id=course_id,
        ))

    logger.info(
        "Awarded %d XP to user %s for forum %s (post %d)",
        xp_gained, user.email, activity_type, forum_post_id,
    )
    return xp_gained


async def _revoke_forum_xp(
    db: AsyncSession,
    user_id,
    tutorial_id,
    activity_type: str,
    xp_amount: int,
    forum_post_id: int,
):
    """Revoke XP when a forum post is deleted."""

    # Get user
    user_result = await db.execute(select(User).filter_by(id=user_id))
    user = user_result.scalars().first()
    if not user:
        return 0

    # Update UserTutorial — only unset the flag if no other posts of this type exist
    remaining = await db.execute(
        select(ForumActivity).filter(
            ForumActivity.user_id == user_id,
            ForumActivity.tutorial_id == tutorial_id,
            ForumActivity.activity_type == activity_type,
            ForumActivity.deleted_on_forum == False,
            ForumActivity.forum_post_id != forum_post_id,
        )
    )
    has_other_posts = remaining.scalars().first() is not None

    from services.xp import recompute_tutorial_xp, recalc_level

    ut_result = await db.execute(
        select(UserTutorial).filter_by(user_id=user_id, tutorial_id=tutorial_id)
    )
    ut = ut_result.scalars().first()

    xp_gained = 0
    if ut:
        # Only unset the flag (and lose the once-per-type XP) when NO other live post of
        # this type remains — otherwise deleting one of several posts must not deduct XP.
        if not has_other_posts:
            if activity_type == "question":
                ut.forum_asked = False
            elif activity_type == "answer":
                ut.forum_answered = False
        xp_gained = recompute_tutorial_xp(ut)  # negative if a flag was unset, else 0
    elif not has_other_posts:
        # No progress row — mirror the award fallback and decrement global XP.
        xp_gained = -xp_amount

    if xp_gained != 0:
        user.xp_total = max(0, user.xp_total + xp_gained)
        recalc_level(user)
        course_id = (await db.execute(
            select(Tutorial.course_id).filter(Tutorial.id == tutorial_id)
        )).scalar()
        db.add(XPEvent(
            user_id=user_id,
            source_type="forum_activity_revoked",
            source_id=str(forum_post_id),
            xp_delta=xp_gained,
            course_id=course_id,
        ))

    logger.info(
        "Revoked %d XP from user %s for deleted forum %s (post %d)",
        xp_gained, user.email, activity_type, forum_post_id,
    )
    return xp_gained


def activity_to_dict(a) -> dict:
    """Serialize a ForumActivity row to the API shape. Shared by the per-tutorial
    and course-wide (grouped) forum-activity endpoints."""
    return {
        "id": a.id,
        "forumPostId": a.forum_post_id,
        "activityType": a.activity_type,
        "title": a.title,
        "forumUrl": a.forum_url,
        "postedAt": a.posted_at.isoformat() if a.posted_at else None,
        "xpAwarded": a.xp_awarded,
        "xpAmount": a.xp_amount,
    }


async def get_forum_activity_for_tutorial(
    db: AsyncSession, user_id, tutorial_id
) -> list[dict]:
    """
    Get all non-deleted forum activity for a specific user + tutorial.
    Used by the frontend to display verified forum posts.
    """
    result = await db.execute(
        select(ForumActivity).filter(
            ForumActivity.user_id == user_id,
            ForumActivity.tutorial_id == tutorial_id,
            ForumActivity.deleted_on_forum == False,
        ).order_by(ForumActivity.posted_at.desc())
    )
    return [activity_to_dict(a) for a in result.scalars().all()]
