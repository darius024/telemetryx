"""Rules Engine for TelemetryX.

Evaluates telemetry events against user-defined rules
and triggers actions when conditions match.
"""

from telemetryx.rules.dsl import evaluate_condition
from telemetryx.rules.engine import RulesEngine
from telemetryx.rules.models import (
    Action,
    ActionType,
    Comparison,
    Condition,
    Operator,
    Rule,
    RuleMatch,
    Severity,
)
from telemetryx.rules.repository import RulesRepository

__all__ = [
    "Action",
    "ActionType",
    "Comparison",
    "Condition",
    "Operator",
    "Rule",
    "RuleMatch",
    "RulesEngine",
    "RulesRepository",
    "Severity",
    "evaluate_condition",
]
