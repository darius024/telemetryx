"""Tests for the Rules Repository."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from telemetryx.rules import (
    Action,
    ActionType,
    Condition,
    Operator,
    Rule,
    RulesRepository,
    Severity,
)


@pytest.fixture
def sample_rule() -> Rule:
    """Create a sample rule for testing."""
    return Rule(
        id=uuid4(),
        name="Test Rule",
        description="A test rule",
        enabled=True,
        priority=100,
        severity=Severity.WARNING,
        condition=Condition(field="value", op=Operator.GT, value=50),
        actions=[Action(type=ActionType.LOG, config={"level": "warn"})],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_db_row(sample_rule: Rule) -> dict:
    """Create a sample database row."""
    return {
        "id": str(sample_rule.id),
        "name": sample_rule.name,
        "description": sample_rule.description,
        "enabled": sample_rule.enabled,
        "priority": sample_rule.priority,
        "severity": sample_rule.severity.value,
        "condition": {"field": "value", "op": ">", "value": 50},
        "actions": [{"type": "log", "config": {"level": "warn"}}],
        "created_at": sample_rule.created_at,
        "updated_at": sample_rule.updated_at,
    }


class TestGetEnabledRules:
    """Test get_enabled_rules method."""

    @pytest.mark.asyncio
    async def test_returns_cached_rules(self, sample_rule: Rule):
        """Uses cache when available."""
        repo = RulesRepository()
        rule_ids = [str(sample_rule.id)]

        with (
            patch("telemetryx.rules.repository.redis") as mock_redis,
            patch("telemetryx.rules.repository.postgres") as mock_postgres,
        ):
            # Cache hit for list
            mock_redis.cache_get = AsyncMock(
                side_effect=[
                    json.dumps(rule_ids),  # List cache hit
                    sample_rule.model_dump_json(),  # Individual rule cache hit
                ]
            )

            rules = await repo.get_enabled_rules()

            assert len(rules) == 1
            assert rules[0].name == sample_rule.name
            mock_postgres.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetches_from_db_on_cache_miss(self, sample_db_row: dict):
        """Fetches from database when cache is empty."""
        repo = RulesRepository()

        with (
            patch("telemetryx.rules.repository.redis") as mock_redis,
            patch("telemetryx.rules.repository.postgres") as mock_postgres,
        ):
            mock_redis.cache_get = AsyncMock(return_value=None)
            mock_redis.cache_set = AsyncMock()
            mock_postgres.execute = AsyncMock(return_value=[sample_db_row])

            rules = await repo.get_enabled_rules()

            assert len(rules) == 1
            assert rules[0].name == "Test Rule"
            mock_postgres.execute.assert_called_once()
            assert mock_redis.cache_set.call_count == 2  # List + individual rule


class TestGetById:
    """Test get_by_id method."""

    @pytest.mark.asyncio
    async def test_returns_cached_rule(self, sample_rule: Rule):
        """Uses cache when available."""
        repo = RulesRepository()

        with patch("telemetryx.rules.repository.redis") as mock_redis:
            mock_redis.cache_get = AsyncMock(return_value=sample_rule.model_dump_json())

            rule = await repo.get_by_id(sample_rule.id)  # type: ignore

            assert rule is not None
            assert rule.name == sample_rule.name

    @pytest.mark.asyncio
    async def test_fetches_from_db_on_cache_miss(self, sample_db_row: dict):
        """Fetches from database when cache is empty."""
        repo = RulesRepository()
        rule_id = UUID(sample_db_row["id"])

        with (
            patch("telemetryx.rules.repository.redis") as mock_redis,
            patch("telemetryx.rules.repository.postgres") as mock_postgres,
        ):
            mock_redis.cache_get = AsyncMock(return_value=None)
            mock_redis.cache_set = AsyncMock()
            mock_postgres.execute = AsyncMock(return_value=[sample_db_row])

            rule = await repo.get_by_id(rule_id)

            assert rule is not None
            assert rule.name == "Test Rule"
            mock_redis.cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """Returns None when rule doesn't exist."""
        repo = RulesRepository()

        with (
            patch("telemetryx.rules.repository.redis") as mock_redis,
            patch("telemetryx.rules.repository.postgres") as mock_postgres,
        ):
            mock_redis.cache_get = AsyncMock(return_value=None)
            mock_postgres.execute = AsyncMock(return_value=[])

            rule = await repo.get_by_id(uuid4())

            assert rule is None


class TestCreate:
    """Test create method."""

    @pytest.mark.asyncio
    async def test_creates_rule(self, sample_rule: Rule, sample_db_row: dict):
        """Successfully creates a rule."""
        repo = RulesRepository()
        sample_rule.id = None  # New rule has no ID

        with (
            patch("telemetryx.rules.repository.redis") as mock_redis,
            patch("telemetryx.rules.repository.postgres") as mock_postgres,
        ):
            mock_redis.cache_delete = AsyncMock()
            mock_postgres.execute = AsyncMock(return_value=[sample_db_row])

            created = await repo.create(sample_rule)

            assert created.id is not None
            assert created.name == sample_rule.name
            mock_redis.cache_delete.assert_called_once_with("rules:enabled")


class TestUpdate:
    """Test update method."""

    @pytest.mark.asyncio
    async def test_updates_rule(self, sample_rule: Rule, sample_db_row: dict):
        """Successfully updates a rule."""
        repo = RulesRepository()

        with (
            patch("telemetryx.rules.repository.redis") as mock_redis,
            patch("telemetryx.rules.repository.postgres") as mock_postgres,
        ):
            mock_redis.cache_delete = AsyncMock()
            mock_postgres.execute = AsyncMock(return_value=[sample_db_row])

            updated = await repo.update(sample_rule)

            assert updated is not None
            assert updated.name == sample_rule.name
            assert mock_redis.cache_delete.call_count == 2  # Rule + list

    @pytest.mark.asyncio
    async def test_returns_none_for_rule_without_id(self, sample_rule: Rule):
        """Returns None when rule has no ID."""
        repo = RulesRepository()
        sample_rule.id = None

        result = await repo.update(sample_rule)

        assert result is None


class TestDelete:
    """Test delete method."""

    @pytest.mark.asyncio
    async def test_deletes_rule(self):
        """Successfully deletes a rule."""
        repo = RulesRepository()
        rule_id = uuid4()

        with (
            patch("telemetryx.rules.repository.redis") as mock_redis,
            patch("telemetryx.rules.repository.postgres") as mock_postgres,
        ):
            mock_redis.cache_delete = AsyncMock()
            mock_postgres.execute = AsyncMock(return_value=[{"id": str(rule_id)}])

            result = await repo.delete(rule_id)

            assert result is True
            assert mock_redis.cache_delete.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        """Returns False when rule doesn't exist."""
        repo = RulesRepository()

        with patch("telemetryx.rules.repository.postgres") as mock_postgres:
            mock_postgres.execute = AsyncMock(return_value=[])

            result = await repo.delete(uuid4())

            assert result is False
