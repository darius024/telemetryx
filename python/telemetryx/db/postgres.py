"""Async PostgreSQL client with connection pooling.

This module provides:
- Connection pool management
- Async query execution
- Transaction support
- Health checks
"""

from contextlib import asynccontextmanager
from typing import Any

from psycopg import AsyncConnection, sql
from psycopg_pool import AsyncConnectionPool

from telemetryx.core import get_logger, get_settings
from telemetryx.core.exceptions import DatabaseError

# Module-level pool instance (initialized on startup)
_pool: AsyncConnectionPool | None = None


async def init_pool() -> None:
    """Initialize the connection pool."""
    global _pool

    settings = get_settings()
    logger = get_logger(__name__)

    if not settings.database_url:
        logger.warning("DATABASE_URL not set, PostgreSQL disabled")
        return

    try:
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=2,
            max_size=10,
            open=False,
        )
        await _pool.open()
        await _pool.wait()

        logger.info(
            "PostreSQL pool initialized",
            min_size=2,
            max_size=10,
        )
    except Exception as e:
        raise DatabaseError(f"Failed to connect to PostreSQL: {e}")


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        get_logger(__name__).info("PostreSQL pool closed")


def get_pool() -> AsyncConnectionPool:
    """Get the connection pool."""
    if _pool is None:
        raise DatabaseError("PostreSQL pool not initialized. Call init_pool() first.")
    return _pool


@asynccontextmanager
async def get_connection():
    """Get a connection from the pool.

    Usage:
        async with get_connection() as conn:
            result = await conn.execute("SELECT 1")

    The connection is automatically returned to the pool when done.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        yield conn

    
async def execute(
    query: str,
    params: tuple[Any, ...] | dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute a query and return results as list of dicts.

    Returns:
        List of rows as dictionaries

    Example:
        # Positional parameters
        users = await execute(
            "SELECT * FROM users WHERE age > %s",
            (18,)
        )

        # Named parameters
        users = await execute(
            "SELECT * FROM users WHERE name = %(name)s",
            {"name": "Alice"}
        )
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)

            # If it's a SELECT, fetch results
            if cur.description is not None:
                columns = [desc[0] for desc in cur.description]
                rows = await cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]

            return []


async def execute_many(
    query: str,
    params_list: list[tuple[Any, ...]],
) -> int:
    """Execute a query multiple times with different parameters.

    Useful for batch inserts.

    Returns:
        Number of rows affected

    Example:
        count = await execute_many(
            "INSERT INTO events (id, type) VALUES (%s, %s)",
            [
                ("evt-1", "click"),
                ("evt-2", "view"),
                ("evt-3", "click"),
            ]
        )
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(query, params_list)
            return cur.rowcount


@asynccontextmanager
async def transaction():
    """Execute queries within a transaction.

    All queries inside the block are committed together,
    or rolled back if an exception occurs.

    Usage:
        async with transaction() as conn:
            await conn.execute("INSERT INTO ...")
            await conn.execute("UPDATE ...")
            # Both committed together
    """
    async with get_connection() as conn:
        async with conn.transaction():
            yield conn


async def health_check() -> bool:
    """Check if PostgreSQL is healthy."""
    if _pool is None:
        return True

    try:
        async with get_connection() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False
        