"""Rules Engine for TelemetryX.

Evaluates telemetry events against user-defined rules
and triggers actions when conditions match.
"""

from telemetryx.rules.dsl import evaluate_condition
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

__all__ = [
    "Action",
    "ActionType",
    "Comparison",
    "Condition",
    "Operator",
    "Rule",
    "RuleMatch",
    "Severity",
    "evaluate_condition",
]
