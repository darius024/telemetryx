"""Tests for the Rules Engine."""

from uuid import uuid4

from telemetryx.rules import (
    Action,
    ActionType,
    Condition,
    Operator,
    Rule,
    RulesEngine,
    Severity,
)


def make_rule(
    name: str,
    field: str,
    op: Operator,
    value: any,
    priority: int = 100,
    enabled: bool = True,
    severity: Severity = Severity.INFO,
) -> Rule:
    """Helper to create a rule for testing."""
    return Rule(
        id=uuid4(),
        name=name,
        condition=Condition(field=field, op=op, value=value),
        actions=[Action(type=ActionType.LOG, config={"level": "info"})],
        priority=priority,
        enabled=enabled,
        severity=severity,
    )


class TestRulesEngine:
    """Test the RulesEngine class."""

    def test_no_rules(self):
        """Engine returns empty list when no rules provided."""
        engine = RulesEngine()
        matches = engine.evaluate({"value": 100}, [])
        assert matches == []

    def test_no_matches(self):
        """Engine returns empty list when no rules match."""
        engine = RulesEngine()
        rules = [make_rule("high-value", "value", Operator.GT, 100)]
        matches = engine.evaluate({"value": 50}, rules)
        assert matches == []

    def test_single_match(self):
        """Engine returns match when rule condition is met."""
        engine = RulesEngine()
        rules = [make_rule("high-value", "value", Operator.GT, 100)]
        matches = engine.evaluate({"value": 150}, rules)

        assert len(matches) == 1
        assert matches[0].rule_name == "high-value"

    def test_multiple_matches(self):
        """Engine returns all matching rules."""
        engine = RulesEngine()
        rules = [
            make_rule("high-value", "value", Operator.GT, 50),
            make_rule("error-status", "status", Operator.EQ, "error"),
            make_rule("low-value", "value", Operator.LT, 10),  # Won't match
        ]
        matches = engine.evaluate({"value": 100, "status": "error"}, rules)

        assert len(matches) == 2
        rule_names = {m.rule_name for m in matches}
        assert rule_names == {"high-value", "error-status"}

    def test_priority_order(self):
        """Matches are returned in priority order."""
        engine = RulesEngine()
        rules = [
            make_rule("low-priority", "value", Operator.GT, 50, priority=200),
            make_rule("high-priority", "value", Operator.GT, 50, priority=10),
            make_rule("medium-priority", "value", Operator.GT, 50, priority=100),
        ]
        matches = engine.evaluate({"value": 100}, rules)

        assert len(matches) == 3
        assert matches[0].rule_name == "high-priority"
        assert matches[1].rule_name == "medium-priority"
        assert matches[2].rule_name == "low-priority"

    def test_disabled_rules_skipped(self):
        """Disabled rules are not evaluated."""
        engine = RulesEngine()
        rules = [
            make_rule("enabled", "value", Operator.GT, 50, enabled=True),
            make_rule("disabled", "value", Operator.GT, 50, enabled=False),
        ]
        matches = engine.evaluate({"value": 100}, rules)

        assert len(matches) == 1
        assert matches[0].rule_name == "enabled"

    def test_severity_preserved(self):
        """Match preserves the rule's severity level."""
        engine = RulesEngine()
        rules = [make_rule("critical", "value", Operator.GT, 50, severity=Severity.CRITICAL)]
        matches = engine.evaluate({"value": 100}, rules)

        assert matches[0].severity == Severity.CRITICAL

    def test_actions_preserved(self):
        """Match preserves the rule's actions."""
        engine = RulesEngine()
        rule = Rule(
            id=uuid4(),
            name="multi-action",
            condition=Condition(field="value", op=Operator.GT, value=50),
            actions=[
                Action(type=ActionType.LOG, config={"level": "error"}),
                Action(type=ActionType.ALERT, config={"channel": "slack"}),
            ],
        )
        matches = engine.evaluate({"value": 100}, [rule])

        assert len(matches[0].actions) == 2
        assert matches[0].actions[0].type == ActionType.LOG
        assert matches[0].actions[1].type == ActionType.ALERT


class TestEvaluateSingle:
    """Test the evaluate_single method."""

    def test_matching_rule(self):
        """Returns RuleMatch when rule matches."""
        engine = RulesEngine()
        rule = make_rule("test", "value", Operator.GT, 50)
        match = engine.evaluate_single({"value": 100}, rule)

        assert match is not None
        assert match.rule_name == "test"

    def test_non_matching_rule(self):
        """Returns None when rule doesn't match."""
        engine = RulesEngine()
        rule = make_rule("test", "value", Operator.GT, 50)
        match = engine.evaluate_single({"value": 10}, rule)

        assert match is None

    def test_disabled_rule(self):
        """Returns None for disabled rule even if condition would match."""
        engine = RulesEngine()
        rule = make_rule("test", "value", Operator.GT, 50, enabled=False)
        match = engine.evaluate_single({"value": 100}, rule)

        assert match is None
