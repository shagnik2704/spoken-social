"""
Scheduler — runs periodic background jobs.

Currently:
  - compute_leaderboard_weekly: every Monday at 00:05 IST
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from database import SessionLocal
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def run_weekly_leaderboard():
    """Execute the compute_leaderboard_weekly() SQL function."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT compute_leaderboard_weekly()"))
        db.commit()
        logger.info("✅ Weekly leaderboard computed successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Weekly leaderboard computation failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start APScheduler with cron jobs."""
    # Every Monday at 00:05 IST (Asia/Kolkata)
    scheduler.add_job(
        run_weekly_leaderboard,
        trigger=CronTrigger(
            day_of_week="mon",
            hour=0,
            minute=5,
            timezone="Asia/Kolkata",
        ),
        id="weekly_leaderboard",
        name="Compute Weekly Leaderboard",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("📅 Scheduler started — weekly leaderboard runs every Monday at 00:05 IST")


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
