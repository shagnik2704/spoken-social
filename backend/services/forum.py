# ============================================================
# Forum Sync Service — shared logic for processing forum events
# ============================================================
# This module is called by:
#   1. Webhook receiver (routes/webhooks.py) — real-time events
#   2. On-login sync (routes/user.py) — on-demand freshness
#   3. Background worker (future ARQ job) — periodic reconciliation
#
# The core function `process_forum_event` is idempotent:
# call it 100 times with the same forum_post_id and it will
# only award XP once.
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


async def _sync_user_tutorial_forum_radios(
    db: AsyncSession,
    *,
    user_id,
    tutorial_id,
    activity_type: str,
) -> None:
    """
    Set forum_asked / forum_answered on UserTutorial when forum activity exists.

    XP is still awarded later by the worker; this only updates the dashboard Yes/No radios
    so they match detected forum posts immediately.
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

    # Find the course by forum_category
    course_result = await db.execute(
        select(Course).filter_by(forum_category=category)
    )
    course = course_result.scalars().first()

    if not course:
        # Fallback: try matching tutorial title directly across all courses
        tut_result = await db.execute(
            select(Tutorial).filter(Tutorial.title.ilike(normalized_name))
        )
        return tut_result.scalars().first()

    # Find tutorial in that course
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
        existing.posted_at = datetime.now(timezone.utc) # Reset 24-hour clock
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

    # 7. Note: We DO NOT award XP here anymore! It stays 0 and False.
    # The 24-hour ARQ background worker will pick it up and award it.
    #
    # Sync dashboard radios (forumAsked / forumAnswered) so the UI shows "Yes" immediately.
    await _sync_user_tutorial_forum_radios(
        db,
        user_id=user.id,
        tutorial_id=tutorial_id,
        activity_type=activity_type,
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

    # Revoke XP if it was awarded
    if activity.xp_awarded and activity.tutorial_id:
        await _revoke_forum_xp(
            db,
            user_id=activity.user_id,
            tutorial_id=activity.tutorial_id,
            activity_type=activity.activity_type,
            xp_amount=activity.xp_amount,
            forum_post_id=forum_post_id,
        )
        activity.xp_awarded = False

    await db.flush()
    return {"status": "deleted", "xp_revoked": activity.xp_amount}


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
    from services.xp import recompute_tutorial_xp

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
        _recalc_level(user)
        db.add(XPEvent(
            user_id=user.id,
            source_type="forum_activity",
            source_id=str(forum_post_id),
            xp_delta=xp_gained,
        ))

    logger.info(
        "Awarded %d XP to user %s for forum %s (post %d)",
        xp_gained, user.email, activity_type, forum_post_id,
    )


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
        return

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

    from services.xp import recompute_tutorial_xp

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
        _recalc_level(user)
        db.add(XPEvent(
            user_id=user_id,
            source_type="forum_activity_revoked",
            source_id=str(forum_post_id),
            xp_delta=xp_gained,
        ))

    logger.info(
        "Revoked %d XP from user %s for deleted forum %s (post %d)",
        xp_gained, user.email, activity_type, forum_post_id,
    )


def _recalc_level(user: User):
    """Recalculate user level from total XP."""
    xp = user.xp_total
    if xp >= 12000:   user.level = 26
    elif xp >= 7000:  user.level = 21
    elif xp >= 3500:  user.level = 16
    elif xp >= 1500:  user.level = 11
    elif xp >= 500:   user.level = 6
    else:             user.level = 1


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
