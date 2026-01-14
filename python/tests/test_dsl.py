"""Tests for the DSL condition evaluator."""

from telemetryx.rules import Condition, Operator, evaluate_condition


class TestSimpleComparisons:
    """Test simple field comparisons."""

    def test_equality(self):
        """Test == operator."""
        cond = Condition(field="status", op=Operator.EQ, value="active")
        assert evaluate_condition(cond, {"status": "active"}) is True
        assert evaluate_condition(cond, {"status": "inactive"}) is False

    def test_not_equal(self):
        """Test != operator."""
        cond = Condition(field="status", op=Operator.NE, value="error")
        assert evaluate_condition(cond, {"status": "ok"}) is True
        assert evaluate_condition(cond, {"status": "error"}) is False

    def test_greater_than(self):
        """Test > operator."""
        cond = Condition(field="value", op=Operator.GT, value=100)
        assert evaluate_condition(cond, {"value": 150}) is True
        assert evaluate_condition(cond, {"value": 100}) is False
        assert evaluate_condition(cond, {"value": 50}) is False

    def test_greater_or_equal(self):
        """Test >= operator."""
        cond = Condition(field="value", op=Operator.GE, value=100)
        assert evaluate_condition(cond, {"value": 150}) is True
        assert evaluate_condition(cond, {"value": 100}) is True
        assert evaluate_condition(cond, {"value": 50}) is False

    def test_less_than(self):
        """Test < operator."""
        cond = Condition(field="value", op=Operator.LT, value=100)
        assert evaluate_condition(cond, {"value": 50}) is True
        assert evaluate_condition(cond, {"value": 100}) is False
        assert evaluate_condition(cond, {"value": 150}) is False

    def test_less_or_equal(self):
        """Test <= operator."""
        cond = Condition(field="value", op=Operator.LE, value=100)
        assert evaluate_condition(cond, {"value": 50}) is True
        assert evaluate_condition(cond, {"value": 100}) is True
        assert evaluate_condition(cond, {"value": 150}) is False


class TestStringOperators:
    """Test string matching operators."""

    def test_contains(self):
        """Test contains operator."""
        cond = Condition(field="message", op=Operator.CONTAINS, value="error")
        assert evaluate_condition(cond, {"message": "An error occurred"}) is True
        assert evaluate_condition(cond, {"message": "All good"}) is False

    def test_startswith(self):
        """Test startswith operator."""
        cond = Condition(field="path", op=Operator.STARTSWITH, value="/api")
        assert evaluate_condition(cond, {"path": "/api/users"}) is True
        assert evaluate_condition(cond, {"path": "/web/home"}) is False

    def test_endswith(self):
        """Test endswith operator."""
        cond = Condition(field="file", op=Operator.ENDSWITH, value=".py")
        assert evaluate_condition(cond, {"file": "main.py"}) is True
        assert evaluate_condition(cond, {"file": "main.js"}) is False

    def test_regex(self):
        """Test regex operator."""
        cond = Condition(field="email", op=Operator.REGEX, value=r"^[\w.]+@\w+\.\w+$")
        assert evaluate_condition(cond, {"email": "test@example.com"}) is True
        assert evaluate_condition(cond, {"email": "not-an-email"}) is False

    def test_in_operator(self):
        """Test in operator (value in list)."""
        cond = Condition(field="status", op=Operator.IN, value=["active", "pending"])
        assert evaluate_condition(cond, {"status": "active"}) is True
        assert evaluate_condition(cond, {"status": "pending"}) is True
        assert evaluate_condition(cond, {"status": "closed"}) is False


class TestLogicalOperators:
    """Test AND/OR logical combinations."""

    def test_and_all_true(self):
        """Test AND with all conditions true."""
        cond = Condition(
            and_=[
                Condition(field="status", op=Operator.EQ, value="active"),
                Condition(field="value", op=Operator.GT, value=50),
            ]
        )
        assert evaluate_condition(cond, {"status": "active", "value": 100}) is True

    def test_and_one_false(self):
        """Test AND with one condition false."""
        cond = Condition(
            and_=[
                Condition(field="status", op=Operator.EQ, value="active"),
                Condition(field="value", op=Operator.GT, value=50),
            ]
        )
        assert evaluate_condition(cond, {"status": "active", "value": 30}) is False

    def test_or_one_true(self):
        """Test OR with one condition true."""
        cond = Condition(
            or_=[
                Condition(field="status", op=Operator.EQ, value="error"),
                Condition(field="value", op=Operator.GT, value=100),
            ]
        )
        assert evaluate_condition(cond, {"status": "ok", "value": 150}) is True

    def test_or_all_false(self):
        """Test OR with all conditions false."""
        cond = Condition(
            or_=[
                Condition(field="status", op=Operator.EQ, value="error"),
                Condition(field="value", op=Operator.GT, value=100),
            ]
        )
        assert evaluate_condition(cond, {"status": "ok", "value": 50}) is False

    def test_nested_logic(self):
        """Test nested AND/OR conditions."""
        # (status == "active" AND value > 50) OR severity == "critical"
        cond = Condition(
            or_=[
                Condition(
                    and_=[
                        Condition(field="status", op=Operator.EQ, value="active"),
                        Condition(field="value", op=Operator.GT, value=50),
                    ]
                ),
                Condition(field="severity", op=Operator.EQ, value="critical"),
            ]
        )
        # First branch true
        assert evaluate_condition(cond, {"status": "active", "value": 100}) is True
        # Second branch true
        assert evaluate_condition(cond, {"severity": "critical"}) is True
        # Neither branch true
        assert evaluate_condition(cond, {"status": "inactive", "value": 30}) is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_field(self):
        """Test condition when field doesn't exist in event."""
        cond = Condition(field="missing", op=Operator.EQ, value="test")
        assert evaluate_condition(cond, {"other": "value"}) is False

    def test_nested_field_access(self):
        """Test dot notation for nested field access."""
        cond = Condition(field="user.role", op=Operator.EQ, value="admin")
        event = {"user": {"role": "admin", "name": "test"}}
        assert evaluate_condition(cond, event) is True

    def test_deeply_nested_field(self):
        """Test deeply nested field access."""
        cond = Condition(field="a.b.c.d", op=Operator.EQ, value=42)
        event = {"a": {"b": {"c": {"d": 42}}}}
        assert evaluate_condition(cond, event) is True

    def test_nested_field_missing(self):
        """Test nested field that doesn't exist."""
        cond = Condition(field="user.missing.field", op=Operator.EQ, value="test")
        assert evaluate_condition(cond, {"user": {"name": "test"}}) is False

    def test_type_mismatch_comparison(self):
        """Test comparison with incompatible types."""
        cond = Condition(field="value", op=Operator.GT, value=100)
        # String vs int comparison should return False, not error
        assert evaluate_condition(cond, {"value": "not-a-number"}) is False

    def test_string_op_on_non_string(self):
        """Test string operator on non-string value."""
        cond = Condition(field="value", op=Operator.CONTAINS, value="test")
        assert evaluate_condition(cond, {"value": 123}) is False

    def test_invalid_regex(self):
        """Test invalid regex pattern."""
        cond = Condition(field="text", op=Operator.REGEX, value="[invalid")
        assert evaluate_condition(cond, {"text": "test"}) is False

    def test_empty_condition(self):
        """Test empty condition (no field, no logical ops)."""
        cond = Condition()
        assert evaluate_condition(cond, {"any": "event"}) is False

    def test_in_with_non_list_value(self):
        """Test IN operator when condition value is not a list."""
        cond = Condition(field="status", op=Operator.IN, value="not-a-list")
        assert evaluate_condition(cond, {"status": "test"}) is False
