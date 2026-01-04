"""Tests for Redis database layer."""

import pytest

from telemetryx.core.exceptions import ConnectionError
from telemetryx.db import redis


class TestRedisClientManagement:
    """Tests for Redis client management."""

    async def test_get_client_not_initialized_raises_error(self):
        """Accessing client before init raises ConnectionError."""
        await redis.close_client()

        with pytest.raises(ConnectionError, match="not initialized"):
            redis.get_client()

    async def test_health_check_without_client_returns_true(self):
        """Health check returns True when client is not initialized.

        This allows graceful degradation when Redis is not configured.
        """
        await redis.close_client()

        result = await redis.health_check()
        assert result is True

    async def test_init_client_without_url_logs_warning(self, monkeypatch):
        """init_client logs warning and returns when REDIS_URL not set."""
        from telemetryx.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.delenv("REDIS_URL", raising=False)

        # Should not raise, just log warning
        await redis.init_client()

        # Client should still be None
        with pytest.raises(ConnectionError, match="not initialized"):
            redis.get_client()

        get_settings.cache_clear()

    async def test_close_client_idempotent(self):
        """close_client can be called multiple times safely."""
        await redis.close_client()
        await redis.close_client()  # Should not raise
        await redis.close_client()  # Should not raise


# Integration tests - only run when TEST_REDIS_URL is set
@pytest.mark.integration
class TestRedisIntegration:
    """Integration tests requiring a real Redis server.

    Run with: TEST_REDIS_URL=redis://... pytest -m integration
    """

    @pytest.fixture(autouse=True)
    async def setup_client(self, monkeypatch, redis_url):
        """Initialize and cleanup client for each test."""
        if not redis_url:
            pytest.skip("TEST_REDIS_URL not set")

        from telemetryx.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("REDIS_URL", redis_url)
        get_settings.cache_clear()

        await redis.init_client()
        yield
        await redis.close_client()
        get_settings.cache_clear()

    @pytest.fixture
    async def clean_keys(self):
        """Track and cleanup test keys after each test."""
        keys = []
        yield keys
        if keys:
            client = redis.get_client()
            await client.delete(*keys)

    async def test_cache_set_and_get(self, clean_keys):
        """Basic cache set and get operations."""
        clean_keys.append("test:cache:basic")

        await redis.cache_set("test:cache:basic", "hello")
        result = await redis.cache_get("test:cache:basic")

        assert result == "hello"

    async def test_cache_get_missing_key(self):
        """Getting a missing key returns None."""
        result = await redis.cache_get("test:nonexistent:key")
        assert result is None

    async def test_cache_delete(self, clean_keys):
        """Delete removes a key."""
        await redis.cache_set("test:cache:delete", "value")
        await redis.cache_delete("test:cache:delete")

        result = await redis.cache_get("test:cache:delete")
        assert result is None

    async def test_cache_get_or_set_miss(self, clean_keys):
        """cache_get_or_set computes value on cache miss."""
        clean_keys.append("test:cache:getorset")

        async def factory():
            return "computed"

        result = await redis.cache_get_or_set("test:cache:getorset", factory)
        assert result == "computed"

    async def test_cache_get_or_set_hit(self, clean_keys):
        """cache_get_or_set returns cached value on hit."""
        clean_keys.append("test:cache:hit")

        await redis.cache_set("test:cache:hit", "cached")

        factory_called = False

        async def factory():
            nonlocal factory_called
            factory_called = True
            return "computed"

        result = await redis.cache_get_or_set("test:cache:hit", factory)
        assert result == "cached"
        assert not factory_called

    async def test_counter_increment(self, clean_keys):
        """Counter increment works correctly."""
        clean_keys.append("test:counter:inc")

        result1 = await redis.counter_increment("test:counter:inc")
        result2 = await redis.counter_increment("test:counter:inc")
        result3 = await redis.counter_increment("test:counter:inc", 5)

        assert result1 == 1
        assert result2 == 2
        assert result3 == 7

    async def test_counter_get(self, clean_keys):
        """Counter get returns current value."""
        clean_keys.append("test:counter:get")

        await redis.counter_increment("test:counter:get", 42)
        result = await redis.counter_get("test:counter:get")

        assert result == 42

    async def test_counter_get_missing(self):
        """Counter get returns 0 for missing key."""
        result = await redis.counter_get("test:counter:missing")
        assert result == 0

    async def test_counter_reset(self, clean_keys):
        """Counter reset sets counter back to 0."""
        clean_keys.append("test:counter:reset")

        await redis.counter_increment("test:counter:reset", 50)
        assert await redis.counter_get("test:counter:reset") == 50

        await redis.counter_reset("test:counter:reset")
        assert await redis.counter_get("test:counter:reset") == 0

    async def test_hash_set_and_get(self, clean_keys):
        """Hash set and get operations."""
        clean_keys.append("test:hash:basic")

        await redis.hash_set("test:hash:basic", {"name": "alice", "age": "30"})
        result = await redis.hash_get("test:hash:basic", "name")

        assert result == "alice"

    async def test_hash_get_all(self, clean_keys):
        """Hash get all returns all fields."""
        clean_keys.append("test:hash:all")

        await redis.hash_set("test:hash:all", {"a": "1", "b": "2"})
        result = await redis.hash_get_all("test:hash:all")

        assert result == {"a": "1", "b": "2"}

    async def test_hash_delete_field(self, clean_keys):
        """Hash delete removes specific fields."""
        clean_keys.append("test:hash:delete")

        await redis.hash_set("test:hash:delete", {"keep": "1", "remove": "2"})
        await redis.hash_delete("test:hash:delete", "remove")

        result = await redis.hash_get_all("test:hash:delete")
        assert result == {"keep": "1"}

    async def test_health_check_with_client(self):
        """Health check returns True when Redis is healthy."""
        result = await redis.health_check()
        assert result is True

    async def test_publish_returns_subscriber_count(self):
        """Publish returns number of subscribers (0 when none)."""
        count = await redis.publish("test:channel", "message")
        assert count == 0  # No subscribers
