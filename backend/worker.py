import asyncio
import json
from arq.connections import RedisSettings
import logging
from datetime import datetime,timedelta,timezone
from arq import cron
from database import SessionLocal
from services.forum import _award_forum_xp
from models.forum_activity import ForumActivity
from sqlalchemy import select

logger=logging.getLogger("spoken-social.worker")
logging.basicConfig(level=logging.INFO)

async def check_pending_xp(ctx):
    logger.info("Running 24 hour XP Sweep")
    threshold_time=datetime.now(timezone.utc)-timedelta(hours=24)

    async with SessionLocal() as db:
        # Find all un-awarded, un-deleted activities older than 24 hours
        result = await db.execute(
            select(ForumActivity).filter(
                ForumActivity.xp_awarded == False,
                ForumActivity.deleted_on_forum == False,
                ForumActivity.posted_at <= threshold_time,
                ForumActivity.tutorial_id.isnot(None),  # Must be mapped
            )
        )
        activities = result.scalars().all()

        # Batch-load the users referenced by pending activities (was 1 query per activity).
        from models.user import User
        user_ids = {a.user_id for a in activities}
        users_by_id = {}
        if user_ids:
            u_res = await db.execute(select(User).filter(User.id.in_(user_ids)))
            users_by_id = {u.id: u for u in u_res.scalars().all()}

        count = 0
        for activity in activities:
            # Grant the XP!
            user = users_by_id.get(activity.user_id)

            if user:
                await _award_forum_xp(
                    db,
                    user,
                    activity.tutorial_id,
                    activity.activity_type,
                    5 if activity.activity_type == "question" else 10,
                    activity.forum_post_id
                )
                activity.xp_awarded = True
                count += 1

        if count > 0:
            await db.commit()
            logger.info("Successfully awarded XP for %d verified posts!", count)
        else:
            logger.info("No pending XP found.")

async def check_xp_invariants(ctx):
    """Daily XP integrity sweep.

    The 2026-08 audit found ~49k XP of unpaid work that had been wrong for four
    months because nothing was checking. This runs the same assertions every
    night: a healthy system logs all-zero counts, and any non-zero value names
    the worst-affected students so the next step is obvious.

    The result is also published to Redis for the backend to expose as
    Prometheus gauges — see integrity_metrics.py. Worker and backend are
    separate processes and prometheus_client gauges are per-process, so the
    value has to travel through something shared.
    """
    from services.integrity import check_xp_integrity, find_drifted_users
    from integrity_metrics import publish

    async with SessionLocal() as db:
        result = await check_xp_integrity(db)

        if result["healthy"]:
            logger.info("XP integrity OK %s", json.dumps(result))
        else:
            worst = await find_drifted_users(db, limit=10)
            logger.error("XP INTEGRITY VIOLATED %s", json.dumps(result))
            for u in worst:
                logger.error(
                    "  drifted: %s has %d, records imply %d (%+d)",
                    u["name"], u["xp_total"], u["implied"], u["drift"],
                )

    await publish(result)
    return result


class WorkerSettings:
    # Use the official ARQ object to point to the Redis container
    redis_settings = RedisSettings(host="redis", port=6379)

    cron_jobs = [
        cron(check_pending_xp, minute={0, 15, 30, 45}),
        # 02:00 IST — after the day's activity, before anyone looks in the morning.
        cron(check_xp_invariants, hour={2}, minute={0}),
    ]

