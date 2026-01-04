"""Async Redis client with common patterns.

This module provides:
- Connection management
- Caching with TTL
- Atomic counters
- Pub/Sub messaging
- Health checks
"""

from redis.asyncio import Redis

from telemetryx.core import get_logger, get_settings
from telemetryx.core.exceptions import ConnectionError

# Module-level client instance
_client: Redis | None = None


async def init_client() -> None:
    """Initialize the Redis client."""
    global _client

    settings = get_settings()
    logger = get_logger(__name__)

    if not settings.redis_url:
        logger.warning("REDIS_URL not set, Redis disabled")
        return

    try:
        _client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,  # Return strings instead of bytes
        )
        # Test the connection
        await _client.ping()

        logger.info("Redis client initialized", url=settings.redis_url.split("@")[-1])
    except Exception as e:
        raise ConnectionError(f"Failed to connect to Redis: {e}") from e


async def close_client() -> None:
    """Close the Redis client."""
    global _client

    if _client is not None:
        await _client.aclose()
        _client = None
        get_logger(__name__).info("Redis client closed")


def get_client() -> Redis:
    """Get the Redis client."""
    if _client is None:
        raise ConnectionError("Redis client not initialized. Call init_client() first.")
    return _client


# ============================================
# Caching Operations
# ============================================


async def cache_get(key: str) -> str | None:
    """Get a cached value."""
    client = get_client()
    return await client.get(key)


async def cache_set(
    key: str,
    value: str,
    ttl_seconds: int | None = None,
) -> None:
    """Set a cached value.

    Example:
        # Cache for 5 minutes
        await cache_set("user:123:profile", json_data, ttl_seconds=300)
    """
    client = get_client()
    await client.set(key, value, ex=ttl_seconds)


async def cache_delete(key: str) -> None:
    """Delete a cached value."""
    client = get_client()
    await client.delete(key)


async def cache_get_or_set(
    key: str,
    factory,
    ttl_seconds: int | None = None,
) -> str:
    """Get from cache, or compute and cache if missing.

    Returns:
        Cached or computed value

    Example:
        async def fetch_user():
            return await db.execute("SELECT * FROM users WHERE id = 123")

        user = await cache_get_or_set("user:123", fetch_user, ttl_seconds=60)
    """
    value = await cache_get(key)
    if value is not None:
        return value

    # Cache miss - compute value
    value = await factory()
    await cache_set(key, value, ttl_seconds)
    return value


# ============================================
# Counter Operations (Atomic)
# ============================================


async def counter_increment(
    key: str,
    amount: int = 1,
    ttl_seconds: int | None = None,
) -> int:
    """Atomically increment a counter.

    Example:
        # Rate limiting: count requests per minute
        count = await counter_increment("rate:user:123", ttl_seconds=60)
        if count > 100:
            raise RateLimitExceeded()
    """
    client = get_client()
    new_value = await client.incrby(key, amount)

    # Set TTL only if this is a new key (value equals increment)
    if ttl_seconds and new_value == amount:
        await client.expire(key, ttl_seconds)

    return new_value


async def counter_get(key: str) -> int:
    """Get current counter value."""
    client = get_client()
    value = await client.get(key)
    return int(value) if value else 0


async def counter_reset(key: str) -> None:
    """Reset a counter to 0."""
    await cache_delete(key)


# ============================================
# Hash Operations (for structured data)
# ============================================


async def hash_get(key: str, field: str) -> str | None:
    """Get a field from a hash."""
    client = get_client()
    return await client.hget(key, field)


async def hash_get_all(key: str) -> dict[str, str]:
    """Get all fields from a hash."""
    client = get_client()
    return await client.hgetall(key)


async def hash_set(key: str, mapping: dict[str, str]) -> None:
    """Set fields in a hash.

    Example:
        await hash_set("rule:123", {
            "name": "High CPU Alert",
            "enabled": "true",
            "threshold": "90",
        })
    """
    client = get_client()
    await client.hset(key, mapping=mapping)


async def hash_delete(key: str, *fields: str) -> None:
    """Delete fields from a hash."""
    client = get_client()
    await client.hdel(key, *fields)


# ============================================
# Pub/Sub (for real-time notifications)
# ============================================


async def publish(channel: str, message: str) -> int:
    """Publish a message to a channel.

    Returns:
        Number of subscribers who received the message

    Example:
        await publish("rules:updated", json.dumps({"rule_id": "123"}))
    """
    client = get_client()
    return await client.publish(channel, message)


# ============================================
# Health Check
# ============================================


async def health_check() -> bool:
    """Check if Redis is healthy."""
    if _client is None:
        return True

    try:
        await _client.ping()
        return True
    except Exception:
        return False
