"""Tests for unified database lifecycle management."""

from telemetryx.db import close_databases, health_check, init_databases


class TestDatabaseLifecycle:
    """Tests for unified database init/close/health_check."""

    async def test_health_check_returns_expected_structure(self):
        """Health check returns dict with postgres, redis, and overall keys."""
        result = await health_check()

        assert "postgres" in result
        assert "redis" in result
        assert "overall" in result
        assert isinstance(result["postgres"], bool)
        assert isinstance(result["redis"], bool)
        assert isinstance(result["overall"], bool)

    async def test_health_check_without_connections(self):
        """Health check works when databases are not configured."""
        # Ensure nothing is initialized
        await close_databases()

        result = await health_check()

        # Without connections, individual checks return True (graceful degradation)
        assert result["postgres"] is True
        assert result["redis"] is True
        assert result["overall"] is True

    async def test_init_databases_without_urls(self, monkeypatch):
        """init_databases works when no URLs are configured."""
        from telemetryx.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        get_settings.cache_clear()

        # Should not raise
        await init_databases()

        # Health check should still work
        result = await health_check()
        assert result["overall"] is True

        await close_databases()
        get_settings.cache_clear()

    async def test_close_databases_idempotent(self):
        """close_databases can be called multiple times safely."""
        await close_databases()
        await close_databases()  # Should not raise
        await close_databases()  # Should not raise

    async def test_init_then_close_databases(self, monkeypatch):
        """Full lifecycle: init then close."""
        from telemetryx.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        get_settings.cache_clear()

        await init_databases()
        await close_databases()

        # Should be able to call again
        await init_databases()
        await close_databases()

        get_settings.cache_clear()
