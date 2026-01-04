"""Database layer for TelemetryX Python Brain.

This module provides unified access to:
- PostgreSQL: Primary data store (rules, events, analytics)
- Redis: Caching, counters, pub/sub

Usage:
    from telemetryx.db import init_databases, close_databases

    # During startup
    await init_databases()

    # During shutdown
    await close_databases()

    # For individual operations
    from telemetryx.db import postgres, redis
    result = await postgres.execute("SELECT * FROM rules")
    await redis.cache_set("key", "value", ttl_seconds=60)
"""

from telemetryx.core import get_logger
from telemetryx.db import postgres, redis

__all__ = [
    # Lifecycle
    "init_databases",
    "close_databases",
    "health_check",
    # Submodules (for direct access)
    "postgres",
    "redis",
]


async def init_databases() -> None:
    """Initialize all database connections.

    Call this once during application startup.
    This function is idempotent - calling it multiple times is safe.

    Missing connection URLs result in warnings, not errors,
    allowing the application to run with reduced functionality.
    """
    logger = get_logger(__name__)
    logger.info("Initializing database connections...")

    await postgres.init_pool()
    await redis.init_client()

    logger.info("Database initialization complete")


async def close_databases() -> None:
    """Close all database connections gracefully.

    Call this during application shutdown to:
    - Drain connection pools
    - Close active connections
    - Release resources

    This function is idempotent - calling it multiple times is safe.
    """
    logger = get_logger(__name__)
    logger.info("Closing database connections...")

    # Close in reverse order of initialization
    await redis.close_client()
    await postgres.close_pool()

    logger.info("Database connections closed")


async def health_check() -> dict[str, bool]:
    """Check health of all database connections.

    Returns:
        Dictionary with health status for each database:
        {
            "postgres": True/False,
            "redis": True/False,
            "overall": True/False  # True only if all are healthy
        }

    Example:
        health = await health_check()
        if not health["overall"]:
            logger.warning("Database health check failed", **health)
    """
    postgres_healthy = await postgres.health_check()
    redis_healthy = await redis.health_check()

    return {
        "postgres": postgres_healthy,
        "redis": redis_healthy,
        "overall": postgres_healthy and redis_healthy,
    }
