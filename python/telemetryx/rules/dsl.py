"""DSL parser and condition evaluation.

Evaluates rule conditions against event data using a JSON-logic
inspired syntax.

Example:
    condition = Condition(field="value", op=Operator.GT, value=100)
    event = {"value": 150, "event_type": "metric"}
    result = evaluate_condition(condition, event)  # True
"""

import re
from typing import Any

from telemetryx.rules.models import Condition, Operator


def evaluate_condition(condition: Condition, event: dict[str, Any]) -> bool:
    """Evaluate a condition against an event.

    Example:
        >>> cond = Condition(field="value", op=Operator.GT, value=100)
        >>> evaluate_condition(cond, {"value": 150})
        True
    """
    # Handle logical operators
    if condition.and_ is not None:
        return all(evaluate_condition(c, event) for c in condition.and_)

    if condition.or_ is not None:
        return any(evaluate_condition(c, event) for c in condition.or_)

    # Handle simple comparison
    if condition.is_comparison():
        return _evaluate_comparison(
            field=condition.field,  # type: ignore[arg-type]
            op=condition.op,  # type: ignore[arg-type]
            value=condition.value,
            event=event,
        )

    # Empty or invalid condition - doesn't match
    return False


def _evaluate_comparison(
    field: str,
    op: Operator,
    value: Any,
    event: dict[str, Any],
) -> bool:
    """Evaluate a single field comparison."""
    # Get field value from event (supports nested fields via dot notation)
    event_value = _get_nested_value(event, field)

    # Field doesn't exist in event
    if event_value is None:
        return False

    # Evaluate based on operator
    match op:
        case Operator.EQ:
            return event_value == value
        case Operator.NE:
            return event_value != value
        case Operator.GT:
            return _safe_compare(event_value, value, lambda a, b: a > b)
        case Operator.GE:
            return _safe_compare(event_value, value, lambda a, b: a >= b)
        case Operator.LT:
            return _safe_compare(event_value, value, lambda a, b: a < b)
        case Operator.LE:
            return _safe_compare(event_value, value, lambda a, b: a <= b)
        case Operator.CONTAINS:
            return _safe_string_op(event_value, value, lambda s, v: v in s)
        case Operator.STARTSWITH:
            return _safe_string_op(event_value, value, lambda s, v: s.startswith(v))
        case Operator.ENDSWITH:
            return _safe_string_op(event_value, value, lambda s, v: s.endswith(v))
        case Operator.REGEX:
            return _safe_regex(event_value, value)
        case Operator.IN:
            return event_value in value if isinstance(value, (list, tuple)) else False
        case _:
            return False


def _get_nested_value(data: dict[str, Any], field: str) -> Any:
    """Get a value from nested dictionary using dot notation.

    Example:
        >>> _get_nested_value({"a": {"b": 1}}, "a.b")
        1
    """
    keys = field.split(".")
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None

    return current


def _safe_compare(a: Any, b: Any, comparator: Any) -> bool:
    """Safely compare two values, handling type mismatches."""
    try:
        return comparator(a, b)
    except TypeError:
        return False


def _safe_string_op(event_value: Any, pattern: Any, operation: Any) -> bool:
    """Safely perform string operation."""
    if not isinstance(event_value, str) or not isinstance(pattern, str):
        return False
    return operation(event_value, pattern)


def _safe_regex(event_value: Any, pattern: Any) -> bool:
    """Safely evaluate regex pattern."""
    if not isinstance(event_value, str) or not isinstance(pattern, str):
        return False
    try:
        return bool(re.search(pattern, event_value))
    except re.error:
        return False
