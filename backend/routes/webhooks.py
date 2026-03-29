# ============================================================
# Webhook Receiver — handles events pushed from the Spoken
# Tutorial Forum (questions asked, answered, deleted).
# ============================================================

import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from database import get_db
from services.forum import process_forum_event, process_forum_delete, find_user_by_email

logger = logging.getLogger("spoken_social.webhooks")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

WEBHOOK_SECRET = os.getenv("FORUM_WEBHOOK_SECRET", "")


def _verify_secret(request: Request):
    """Verify the webhook secret matches."""
    if not WEBHOOK_SECRET:
        # No secret configured — accept all (dev mode)
        logger.warning("FORUM_WEBHOOK_SECRET not set — accepting all webhooks (dev mode)")
        return

    incoming = request.headers.get("X-Webhook-Secret", "")
    if incoming != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


@router.post("/forum")
async def forum_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receives webhook events from the Spoken Tutorial Forum.

    Events:
      - question_created: a student asked a new question
      - answer_created:   a student posted an answer
      - question_deleted: a question was removed
      - answer_deleted:   an answer was removed
    """

    _verify_secret(request)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing 'event' field")

    logger.info("Forum webhook received: %s (post_id=%s)", event, payload.get("resource_id"))
    logger.info("Payload data: %s", payload)

    # ── Handle create events ──
    if event in ("question_created", "answer_created"):
        activity_type = "question" if event == "question_created" else "answer"

        # The forum sends user_id (integer) — we need to resolve to email.
        # If the forum includes 'email', use it directly. Otherwise, we can't match.
        user_email = payload.get("email")
        if not user_email:
            # Try to find user by forum user_id if we have a mapping
            logger.warning("Webhook missing 'email' field — cannot match user (post_id=%s)", payload.get("resource_id"))
            return {"status": "ignored", "reason": "no_email"}

        # Parse timestamp
        posted_at = None
        ts = payload.get("timestamp")
        if ts:
            try:
                posted_at = datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                posted_at = datetime.now(timezone.utc)

        result = await process_forum_event(
            db,
            forum_post_id=payload.get("resource_id", 0),
            activity_type=activity_type,
            user_email=user_email,
            category=payload.get("category", ""),
            tutorial_name=payload.get("tutorial", ""),
            title=payload.get("title"),
            posted_at=posted_at,
        )

        await db.commit()
        if result.get("status") in ("ignored", "skipped"):
            logger.warning("Webhook %s: %s (reason: %s)", event, result.get("status"), result.get("reason"))
        else:
            logger.info("Webhook processed: %s → %s", event, result.get("status"))
        return result

    # ── Handle delete events ──
    elif event in ("question_deleted", "answer_deleted"):
        activity_type = "question" if event == "question_deleted" else "answer"

        result = await process_forum_delete(
            db,
            forum_post_id=payload.get("resource_id", 0),
            activity_type=activity_type,
        )

        await db.commit()
        logger.info("Webhook processed: %s → %s", event, result.get("status"))
        return result

    else:
        logger.warning("Unknown webhook event: %s", event)
        return {"status": "ignored", "reason": f"unknown_event: {event}"}
