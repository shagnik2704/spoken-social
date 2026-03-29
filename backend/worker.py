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
        
        count = 0
        for activity in activities:
            # Grant the XP! 
            # (Note: we use the related user fetched via joins or directly inside the func)
            # You might need to adjust _award_forum_xp to fetch the User if not passed!
            from models.user import User
            user_result = await db.execute(select(User).filter_by(id=activity.user_id))
            user = user_result.scalars().first()
            
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

