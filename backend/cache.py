import os
import json
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

async def get_cached(key:str):
    try:
        r = redis.Redis(connection_pool=pool)
        val = await r.get(key)
        return json.loads(val) if val else None

    except Exception as e:
        logger.warning(f"redis GET failed for '{key}':'{e}'")
        return None

async def set_cached(key:str,data,ttl:int = 300):
    try:
        r = redis.Redis(connection_pool=pool)
        await r.setex(key,ttl,json.dumps(data,default=str))
    
    except Exception as e:
        logger.warning(f"redis SET failed for '{key}':'{e}'")



