"""Rules Repository - PostgreSQL storage with Redis caching.

Example:
    repo = RulesRepository()
    rules = await repo.get_enabled_rules()
    rule = await repo.get_by_id(rule_id)
"""

import json
from uuid import UUID

from telemetryx.core import get_logger
from telemetryx.db import postgres, redis
from telemetryx.rules.models import Rule

# Cache TTLs
RULES_LIST_TTL = 60  # 1 minute for list of enabled rule IDs
RULE_CACHE_TTL = 300  # 5 minutes for individual rules


class RulesRepository:
    """Repository for rule CRUD operations with caching."""

    def __init__(self) -> None:
        self._logger = get_logger(__name__)

    async def get_enabled_rules(self) -> list[Rule]:
        """Get all enabled rules, using cache when available."""
        # Check cache for rule IDs
        cached_ids = await redis.cache_get("rules:enabled")
        if cached_ids:
            rule_ids = json.loads(cached_ids)
            return await self._get_rules_by_ids(rule_ids)

        # Fetch from database
        rows = await postgres.execute(
            """
            SELECT id, name, description, enabled, priority, severity,
                   condition, actions, created_at, updated_at
            FROM rules
            WHERE enabled = true
            ORDER BY priority ASC
            """
        )

        rules = [self._row_to_rule(row) for row in rows]

        # Cache the IDs
        rule_ids = [str(r.id) for r in rules]
        await redis.cache_set("rules:enabled", json.dumps(rule_ids), RULES_LIST_TTL)

        # Cache individual rules
        for rule in rules:
            await self._cache_rule(rule)

        return rules

    async def get_by_id(self, rule_id: UUID) -> Rule | None:
        """Get a single rule by ID, using cache when available."""
        cache_key = f"rules:id:{rule_id}"

        # Check cache
        cached = await redis.cache_get(cache_key)
        if cached:
            return Rule.model_validate_json(cached)

        # Fetch from database
        rows = await postgres.execute(
            """
            SELECT id, name, description, enabled, priority, severity,
                   condition, actions, created_at, updated_at
            FROM rules
            WHERE id = %s
            """,
            (str(rule_id),),
        )

        if not rows:
            return None

        rule = self._row_to_rule(rows[0])
        await self._cache_rule(rule)
        return rule

    async def create(self, rule: Rule) -> Rule:
        """Create a new rule."""
        rows = await postgres.execute(
            """
            INSERT INTO rules (name, description, enabled, priority, severity, condition, actions)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, description, enabled, priority, severity,
                      condition, actions, created_at, updated_at
            """,
            (
                rule.name,
                rule.description,
                rule.enabled,
                rule.priority,
                rule.severity.value,
                json.dumps(rule.condition.model_dump(by_alias=True, exclude_none=True)),
                json.dumps([a.model_dump() for a in rule.actions]),
            ),
        )

        created_rule = self._row_to_rule(rows[0])
        await self._invalidate_list_cache()
        self._logger.info(
            "Rule created", rule_id=str(created_rule.id), name=created_rule.name
        )
        return created_rule

    async def update(self, rule: Rule) -> Rule | None:
        """Update an existing rule."""
        if rule.id is None:
            return None

        rows = await postgres.execute(
            """
            UPDATE rules
            SET name = %s, description = %s, enabled = %s, priority = %s,
                severity = %s, condition = %s, actions = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, name, description, enabled, priority, severity,
                      condition, actions, created_at, updated_at
            """,
            (
                rule.name,
                rule.description,
                rule.enabled,
                rule.priority,
                rule.severity.value,
                json.dumps(rule.condition.model_dump(by_alias=True, exclude_none=True)),
                json.dumps([a.model_dump() for a in rule.actions]),
                str(rule.id),
            ),
        )

        if not rows:
            return None

        updated_rule = self._row_to_rule(rows[0])
        await self._invalidate_rule_cache(rule.id)
        await self._invalidate_list_cache()
        self._logger.info("Rule updated", rule_id=str(rule.id), name=rule.name)
        return updated_rule

    async def delete(self, rule_id: UUID) -> bool:
        """Delete a rule by ID."""
        rows = await postgres.execute(
            "DELETE FROM rules WHERE id = %s RETURNING id",
            (str(rule_id),),
        )

        if rows:
            await self._invalidate_rule_cache(rule_id)
            await self._invalidate_list_cache()
            self._logger.info("Rule deleted", rule_id=str(rule_id))
            return True
        return False

    async def _get_rules_by_ids(self, rule_ids: list[str]) -> list[Rule]:
        """Fetch multiple rules by ID, using cache."""
        rules = []
        uncached_ids = []

        # Try cache first
        for rule_id in rule_ids:
            cached = await redis.cache_get(f"rules:id:{rule_id}")
            if cached:
                rules.append(Rule.model_validate_json(cached))
            else:
                uncached_ids.append(rule_id)

        # Fetch uncached from database
        if uncached_ids:
            placeholders = ",".join(["%s"] * len(uncached_ids))
            rows = await postgres.execute(
                f"""
                SELECT id, name, description, enabled, priority, severity,
                       condition, actions, created_at, updated_at
                FROM rules
                WHERE id IN ({placeholders})
                """,
                tuple(uncached_ids),
            )

            for row in rows:
                rule = self._row_to_rule(row)
                await self._cache_rule(rule)
                rules.append(rule)

        # Sort by priority
        return sorted(rules, key=lambda r: r.priority)

    def _row_to_rule(self, row: dict) -> Rule:
        """Convert database row to Rule model."""
        condition_data = row["condition"]
        if isinstance(condition_data, str):
            condition_data = json.loads(condition_data)

        actions_data = row["actions"]
        if isinstance(actions_data, str):
            actions_data = json.loads(actions_data)

        return Rule(
            id=UUID(str(row["id"])) if row["id"] else None,
            name=row["name"],
            description=row["description"] or "",
            enabled=row["enabled"],
            priority=row["priority"],
            severity=row["severity"],
            condition=condition_data,
            actions=actions_data,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def _cache_rule(self, rule: Rule) -> None:
        """Cache a single rule."""
        await redis.cache_set(
            f"rules:id:{rule.id}",
            rule.model_dump_json(),
            RULE_CACHE_TTL,
        )

    async def _invalidate_rule_cache(self, rule_id: UUID) -> None:
        """Invalidate cache for a single rule."""
        await redis.cache_delete(f"rules:id:{rule_id}")

    async def _invalidate_list_cache(self) -> None:
        """Invalidate the enabled rules list cache."""
        await redis.cache_delete("rules:enabled")
