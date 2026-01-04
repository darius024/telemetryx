"""Tests to verify proto generation and imports work correctly."""


class TestProtoImports:
    """Verify all proto modules can be imported."""

    def test_import_common_pb2(self) -> None:
        """common_pb2 should be importable."""
        from telemetryx.proto import common_pb2

        # Verify key types exist
        assert hasattr(common_pb2, "Event")
        assert hasattr(common_pb2, "HealthCheckRequest")
        assert hasattr(common_pb2, "HealthCheckResponse")

    def test_import_rules_pb2(self) -> None:
        """rules_pb2 should be importable."""
        from telemetryx.proto import rules_pb2

        assert hasattr(rules_pb2, "EvaluateRequest")
        assert hasattr(rules_pb2, "EvaluateResponse")
        assert hasattr(rules_pb2, "RuleMatch")
        assert hasattr(rules_pb2, "Severity")

    def test_import_analytics_pb2(self) -> None:
        """analytics_pb2 should be importable."""
        from telemetryx.proto import analytics_pb2

        assert hasattr(analytics_pb2, "DetectAnomaliesRequest")
        assert hasattr(analytics_pb2, "DetectAnomaliesResponse")
        assert hasattr(analytics_pb2, "AnomalyResult")

    def test_import_grpc_servicers(self) -> None:
        """gRPC servicer classes should be importable."""
        from telemetryx.proto import analytics_pb2_grpc, rules_pb2_grpc

        assert hasattr(rules_pb2_grpc, "RulesServiceServicer")
        assert hasattr(analytics_pb2_grpc, "AnalyticsServiceServicer")


class TestProtoMessages:
    """Test proto message creation."""

    def test_create_event(self) -> None:
        """Should be able to create Event message."""
        from telemetryx.proto import common_pb2

        event = common_pb2.Event(
            id="test-123",
            event_type="test",
            timestamp=1704307200000,
            source="test-source",
        )

        assert event.id == "test-123"
        assert event.event_type == "test"
        assert event.timestamp == 1704307200000

    def test_create_rule_match(self) -> None:
        """Should be able to create RuleMatch with nested Action."""
        from telemetryx.proto import rules_pb2

        match = rules_pb2.RuleMatch(
            rule_id="rule-1",
            rule_name="Test Rule",
            severity=rules_pb2.WARNING,
            actions=[
                rules_pb2.Action(action_type="log", config="{}"),
            ],
        )

        assert match.rule_id == "rule-1"
        assert match.severity == rules_pb2.WARNING
        assert len(match.actions) == 1
