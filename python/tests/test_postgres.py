"""Tests for PostgreSQL database layer."""

import pytest

from telemetryx.core.exceptions import DatabaseError
from telemetryx.db import postgres


class TestPostgresPoolManagement:
    """Tests for PostgreSQL connection pool management."""

    async def test_get_pool_not_initialized_raises_error(self):
        """Accessing pool before init raises DatabaseError."""
        # Ensure pool is not initialized
        await postgres.close_pool()

        with pytest.raises(DatabaseError, match="not initialized"):
            postgres.get_pool()

    async def test_health_check_without_pool_returns_true(self):
        """Health check returns True when pool is not initialized.

        This allows graceful degradation when database is not configured.
        """
        await postgres.close_pool()

        result = await postgres.health_check()
        assert result is True

    async def test_init_pool_without_url_logs_warning(self, monkeypatch):
        """init_pool logs warning and returns when DATABASE_URL not set."""
        # Clear any existing settings cache
        from telemetryx.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.delenv("DATABASE_URL", raising=False)

        # Should not raise, just log warning
        await postgres.init_pool()

        # Pool should still be None
        with pytest.raises(DatabaseError, match="not initialized"):
            postgres.get_pool()

        get_settings.cache_clear()

    async def test_close_pool_idempotent(self):
        """close_pool can be called multiple times safely."""
        await postgres.close_pool()
        await postgres.close_pool()  # Should not raise
        await postgres.close_pool()  # Should not raise


# Integration tests - only run when TEST_DATABASE_URL is set
@pytest.mark.integration
class TestPostgresIntegration:
    """Integration tests requiring a real PostgreSQL database.

    Run with: TEST_DATABASE_URL=postgres://... pytest -m integration
    """

    @pytest.fixture(autouse=True)
    async def setup_pool(self, monkeypatch, postgres_url):
        """Initialize and cleanup pool for each test."""
        if not postgres_url:
            pytest.skip("TEST_DATABASE_URL not set")

        from telemetryx.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", postgres_url)
        get_settings.cache_clear()

        await postgres.init_pool()
        yield
        await postgres.close_pool()
        get_settings.cache_clear()

    async def test_execute_simple_select(self):
        """Execute a simple SELECT query."""
        result = await postgres.execute("SELECT 1 as num, 'hello' as greeting")

        assert len(result) == 1
        assert result[0]["num"] == 1
        assert result[0]["greeting"] == "hello"

    async def test_execute_with_positional_params(self):
        """Execute query with positional parameters."""
        result = await postgres.execute(
            "SELECT %s::int as a, %s::text as b",
            (42, "test"),
        )

        assert result[0]["a"] == 42
        assert result[0]["b"] == "test"

    async def test_execute_with_named_params(self):
        """Execute query with named parameters."""
        result = await postgres.execute(
            "SELECT %(num)s::int as num",
            {"num": 100},
        )

        assert result[0]["num"] == 100

    async def test_health_check_with_pool(self):
        """Health check returns True when pool is healthy."""
        result = await postgres.health_check()
        assert result is True

    async def test_connection_context_manager(self):
        """Connection context manager works correctly."""
        async with postgres.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                assert result[0] == 1

    async def test_transaction_commit(self):
        """Transactions commit on success."""
        # Create temp table
        await postgres.execute("CREATE TEMP TABLE test_tx (id int PRIMARY KEY, name text)")

        async with postgres.transaction() as conn:
            await conn.execute("INSERT INTO test_tx VALUES (1, 'alice')")
            await conn.execute("INSERT INTO test_tx VALUES (2, 'bob')")

        # Verify committed
        result = await postgres.execute("SELECT * FROM test_tx ORDER BY id")
        assert len(result) == 2
        assert result[0]["name"] == "alice"

    async def test_transaction_rollback_on_error(self):
        """Transactions rollback on exception."""
        await postgres.execute("CREATE TEMP TABLE test_rollback (id int PRIMARY KEY)")

        with pytest.raises(ValueError):
            async with postgres.transaction() as conn:
                await conn.execute("INSERT INTO test_rollback VALUES (1)")
                raise ValueError("Simulated error")

        # Verify rolled back
        result = await postgres.execute("SELECT * FROM test_rollback")
        assert len(result) == 0

    async def test_execute_many_batch_insert(self):
        """execute_many performs batch inserts correctly."""
        await postgres.execute("CREATE TEMP TABLE test_batch (id int PRIMARY KEY, name text)")

        count = await postgres.execute_many(
            "INSERT INTO test_batch (id, name) VALUES (%s, %s)",
            [(1, "alice"), (2, "bob"), (3, "charlie")],
        )

        assert count == 3

        result = await postgres.execute("SELECT * FROM test_batch ORDER BY id")
        assert len(result) == 3
        assert result[0]["name"] == "alice"
        assert result[2]["name"] == "charlie"
