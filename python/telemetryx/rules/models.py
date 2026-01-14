"""Pydantic models for the Rules Engine.

Defines the data structures for rules, conditions, and actions.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Alert severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Operator(str, Enum):
    """Supported comparison operators for conditions."""

    EQ = "=="
    NE = "!="
    GT = ">"
    GE = ">="
    LT = "<"
    LE = "<="
    CONTAINS = "contains"
    STARTSWITH = "startswith"
    ENDSWITH = "endswith"
    REGEX = "regex"
    IN = "in"


class ActionType(str, Enum):
    """Types of actions that can be triggered."""

    LOG = "log"
    ALERT = "alert"
    WEBHOOK = "webhook"


class Action(BaseModel):
    """Action to execute when a rule matches.

    Attributes:
        type: The action type (log, alert, webhook)
        config: Action-specific configuration
    """

    type: ActionType
    config: dict[str, Any] = Field(default_factory=dict)


class Comparison(BaseModel):
    """A single field comparison.

    Example:
        {"field": "value", "op": ">", "value": 100}
    """

    field: str
    op: Operator
    value: Any


class Condition(BaseModel):
    """Rule condition using JSON-logic style DSL.

    Can be either:
    - A simple comparison: {"field": "x", "op": "==", "value": 1}
    - A logical group: {"and": [...]} or {"or": [...]}

    Attributes:
        field: Field name to compare (for simple comparison)
        op: Comparison operator (for simple comparison)
        value: Value to compare against (for simple comparison)
        and_: List of conditions that must ALL match
        or_: List of conditions where ANY must match
    """

    field: str | None = None
    op: Operator | None = None
    value: Any | None = None
    and_: list["Condition"] | None = Field(default=None, alias="and")
    or_: list["Condition"] | None = Field(default=None, alias="or")

    model_config = {"populate_by_name": True}

    def is_comparison(self) -> bool:
        """Check if this is a simple comparison condition."""
        return self.field is not None and self.op is not None

    def is_logical(self) -> bool:
        """Check if this is a logical group (and/or)."""
        return self.and_ is not None or self.or_ is not None


class Rule(BaseModel):
    """A rule that evaluates events and triggers actions.

    Attributes:
        id: Unique identifier
        name: Human-readable name
        description: What this rule detects
        enabled: Whether the rule is active
        priority: Evaluation order (lower = first)
        severity: Alert severity when triggered
        condition: When to trigger (DSL condition)
        actions: What to do when triggered
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    id: UUID | None = None
    name: str
    description: str = ""
    enabled: bool = True
    priority: int = Field(default=100, ge=0)
    severity: Severity = Severity.INFO
    condition: Condition
    actions: list[Action] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RuleMatch(BaseModel):
    """Result when a rule matches an event.

    Attributes:
        rule_id: ID of the matched rule
        rule_name: Name of the matched rule
        severity: Severity level
        actions: Actions to execute
    """

    rule_id: UUID
    rule_name: str
    severity: Severity
    actions: list[Action]
