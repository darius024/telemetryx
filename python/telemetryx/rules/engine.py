"""Rules Engine - orchestrates event evaluation against rules.

Example:
    engine = RulesEngine()
    matches = engine.evaluate(event, rules)
    for match in matches:
        print(f"Rule {match.rule_name} matched with severity {match.severity}")
"""

from typing import Any

from telemetryx.core import get_logger
from telemetryx.rules.dsl import evaluate_condition
from telemetryx.rules.models import Rule, RuleMatch


class RulesEngine:
    """Evaluates events against a set of rules.

    Rules are evaluated in priority order (lower priority number = evaluated first).
    All matching rules are returned as RuleMatch objects.
    """

    def __init__(self) -> None:
        self._logger = get_logger(__name__)

    def evaluate(
        self,
        event: dict[str, Any],
        rules: list[Rule],
    ) -> list[RuleMatch]:
        """Evaluate an event against a list of rules.

        Rules are sorted by priority and only enabled rules are evaluated.
        Returns all rules that match the event.
        """
        matches: list[RuleMatch] = []

        # Sort by priority (lower = higher priority, evaluated first)
        sorted_rules = sorted(
            (r for r in rules if r.enabled),
            key=lambda r: r.priority,
        )

        for rule in sorted_rules:
            try:
                if evaluate_condition(rule.condition, event):
                    match = RuleMatch(
                        rule_id=rule.id,  # type: ignore[arg-type]
                        rule_name=rule.name,
                        severity=rule.severity,
                        actions=rule.actions,
                    )
                    matches.append(match)
                    self._logger.debug(
                        "Rule matched",
                        rule_id=str(rule.id),
                        rule_name=rule.name,
                        severity=rule.severity.value,
                    )
            except Exception as e:
                self._logger.warning(
                    "Rule evaluation failed",
                    rule_id=str(rule.id),
                    rule_name=rule.name,
                    error=str(e),
                )

        return matches

    def evaluate_single(self, event: dict[str, Any], rule: Rule) -> RuleMatch | None:
        """Evaluate an event against a single rule."""
        if not rule.enabled:
            return None

        try:
            if evaluate_condition(rule.condition, event):
                return RuleMatch(
                    rule_id=rule.id,  # type: ignore[arg-type]
                    rule_name=rule.name,
                    severity=rule.severity,
                    actions=rule.actions,
                )
        except Exception as e:
            self._logger.warning(
                "Rule evaluation failed",
                rule_id=str(rule.id),
                rule_name=rule.name,
                error=str(e),
            )

        return None
