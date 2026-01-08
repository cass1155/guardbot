from redis.asyncio import Redis
from bot.core.config import settings
from bot.core.memory_cache import MemoryCache

if settings.redis_url:
    redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
else:
    redis_client = MemoryCache()

async def get_redis():
    return redis_client

async def close_redis():
    await redis_client.close()
