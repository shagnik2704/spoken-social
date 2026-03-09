import os 
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379")
pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

LEADERBOARD_KEY="lb:xp"
USER_META_PREFIX="lb:meta:"

async def update_user_xp(user_id:str,xp_total:int,meta:dict):
    try:
        r = redis.Redis(connection_pool=pool)
        await r.zadd(LEADERBOARD_KEY,{user_id:xp_total})
        await r.hset(f"{USER_META_PREFIX}{user_id}",mapping=meta)
    
    except Exception as e:
        logger.warning(f"Leaderboard update failed {e}")


async def get_top(limit: int = 100)->list[dict]:
    try:
        r = redis.Redis(connection_pool=pool)
        top = await r.zrevrange(LEADERBOARD_KEY,0,limit-1,withscores=True)

        results=[]
        for rank,(user_id,score) in enumerate(top,start=1):
            meta = await r.hgetall(f"{USER_META_PREFIX}{user_id}")
            results.append({
                "id": user_id,
                "rank": rank,
                "xp": int(score),
                "name": meta.get("name", ""),
                "username": meta.get("username", ""),
                "level": int(meta.get("level", 1)),
                "levelTitle": meta.get("levelTitle", "Beginner"),
                "xpLastWeek": int(meta.get("xpLastWeek", 0)),
                "trend": "same",
                "trendDelta": 0,
            })

        return results
    
    except Exception as e:
        logger.warning(f"Leaderboard fetch failed cause of :{e}")
        return []


async def seed_from_db(db):
    from models import User
    from sqlalchemy import select

    try:
        result = await db.execute(select(User).filter(User.role == "student"))
        users = result.scalars().all()
        r = redis.Redis(connection_pool=pool)
        for user in users:
            uid = str(user.id)
            await r.zadd(LEADERBOARD_KEY, {uid: user.xp_total})
            await r.hset(f"{USER_META_PREFIX}{uid}", mapping={
                "name": user.display_name or "",
                "username": user.username or "",
                "level": user.level,
                "levelTitle": user._level_title(),
                "xpLastWeek": user.xp_last_week,
            })
        logger.warning(f"Seeded leaderboard with {len(users)} students")

    except Exception as e:
        logger.warning(f"Unable to seed leaderboard because of {e}")
        




