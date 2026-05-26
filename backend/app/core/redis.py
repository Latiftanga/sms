from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings

_pool: ConnectionPool | None = None
_redis: Redis | None = None


async def init_redis() -> None:
    global _pool, _redis
    _pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=20,
        decode_responses=True,
    )
    _redis = Redis(connection_pool=_pool)


async def close_redis() -> None:
    global _redis, _pool
    if _redis:
        await _redis.aclose()
    if _pool:
        await _pool.aclose()
    _redis = None
    _pool = None


def get_redis() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized — call init_redis() first")
    return _redis


async def check_redis_health() -> bool:
    try:
        r = get_redis()
        return await r.ping()
    except Exception:
        return False


# ── Helpers ───────────────────────────────────────────────────────

async def invalidate_permission_cache(redis: Redis, user_id: str) -> None:
    """Drop the entire permission cache entry for a user on any permission change."""
    await redis.delete(f"perm:{user_id}")


async def invalidate_school_permission_cache(redis: Redis, school_id: str) -> None:
    """Drop all staff permission caches for a school (e.g. on position rename)."""
    async for key in redis.scan_iter(f"perm:school:{school_id}:*"):
        await redis.delete(key)
