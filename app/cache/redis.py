from redis.asyncio import Redis

from app.core.config import settings


def build_redis_client() -> Redis:
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
        protocol=2,
    )


redis_client = build_redis_client()
