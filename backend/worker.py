import asyncio
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

class WorkerSettings:
    # Use the official ARQ object to point to the Redis container
    redis_settings = RedisSettings(host="redis", port=6379)
    
    cron_jobs = [
        cron(check_pending_xp,minute={0,15,30,45})
    ]

