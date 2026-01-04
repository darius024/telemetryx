"""Tests for gRPC service handlers."""

import pytest

from telemetryx.proto import rules_pb2, analytics_pb2, common_pb2
from telemetryx.grpc_server.handlers import (
    RulesServiceHandler,
    AnalyticsServiceHandler,
)


class TestRulesServiceHandler:
    """Tests for RulesServiceHandler."""

    @pytest.fixture
    def handler(self) -> RulesServiceHandler:
        """Create a handler instance."""
        return RulesServiceHandler()

    @pytest.mark.asyncio
    async def test_evaluate_event_returns_response(
        self,
        handler: RulesServiceHandler,
        sample_event_data: dict,
    ) -> None:
        """EvaluateEvent should return a valid response."""
        # Create a proto Event from test data
        event = rules_pb2.EvaluateRequest(
            event=common_pb2.Event(
                id=sample_event_data["id"],
                event_type=sample_event_data["event_type"],
                timestamp=sample_event_data["timestamp"],
                source=sample_event_data["source"],
            )
        )
        
        # Call the handler (context=None is okay for unit tests)
        response = await handler.EvaluateEvent(event, context=None)
        
        # Verify response structure
        assert isinstance(response, rules_pb2.EvaluateResponse)
        assert response.evaluation_time_ms >= 0

    @pytest.mark.asyncio
    async def test_evaluate_error_event_matches_rule(
        self,
        handler: RulesServiceHandler,
        sample_error_event_data: dict,
    ) -> None:
        """Error events should match the placeholder error rule."""
        event = rules_pb2.EvaluateRequest(
            event=common_pb2.Event(
                id=sample_error_event_data["id"],
                event_type=sample_error_event_data["event_type"],
                timestamp=sample_error_event_data["timestamp"],
                source=sample_error_event_data["source"],
            )
        )
        
        response = await handler.EvaluateEvent(event, context=None)
        
        # The placeholder logic matches error events
        assert len(response.matches) == 1
        assert response.matches[0].rule_id == "rule-001"
        assert response.matches[0].severity == rules_pb2.WARNING

    @pytest.mark.asyncio
    async def test_evaluate_normal_event_no_matches(
        self,
        handler: RulesServiceHandler,
        sample_event_data: dict,
    ) -> None:
        """Normal events should not match any rules (placeholder logic)."""
        event = rules_pb2.EvaluateRequest(
            event=common_pb2.Event(
                id=sample_event_data["id"],
                event_type=sample_event_data["event_type"],
                timestamp=sample_event_data["timestamp"],
            )
        )
        
        response = await handler.EvaluateEvent(event, context=None)
        
        assert len(response.matches) == 0


class TestAnalyticsServiceHandler:
    """Tests for AnalyticsServiceHandler."""

    @pytest.fixture
    def handler(self) -> AnalyticsServiceHandler:
        """Create a handler instance."""
        return AnalyticsServiceHandler()

    @pytest.mark.asyncio
    async def test_detect_anomalies_returns_results(
        self,
        handler: AnalyticsServiceHandler,
        sample_event_data: dict,
    ) -> None:
        """DetectAnomalies should return results for each event."""
        request = analytics_pb2.DetectAnomaliesRequest(
            events=[
                common_pb2.Event(
                    id=sample_event_data["id"],
                    event_type=sample_event_data["event_type"],
                )
            ],
            model_name="default",
            sensitivity=0.5,
        )
        
        response = await handler.DetectAnomalies(request, context=None)
        
        assert isinstance(response, analytics_pb2.DetectAnomaliesResponse)
        assert len(response.results) == 1
        assert response.results[0].event_id == sample_event_data["id"]
        assert response.inference_time_ms >= 0

    @pytest.mark.asyncio
    async def test_detect_anomalies_flags_errors(
        self,
        handler: AnalyticsServiceHandler,
        sample_error_event_data: dict,
    ) -> None:
        """Error events should be flagged as anomalies (placeholder logic)."""
        request = analytics_pb2.DetectAnomaliesRequest(
            events=[
                common_pb2.Event(
                    id=sample_error_event_data["id"],
                    event_type=sample_error_event_data["event_type"],
                )
            ],
        )
        
        response = await handler.DetectAnomalies(request, context=None)
        
        assert response.results[0].is_anomaly is True
        assert response.results[0].anomaly_score > 0.5

    @pytest.mark.asyncio
    async def test_detect_anomalies_empty_events(
        self,
        handler: AnalyticsServiceHandler,
    ) -> None:
        """Empty event list should return empty results."""
        request = analytics_pb2.DetectAnomaliesRequest(events=[])
        
        response = await handler.DetectAnomalies(request, context=None)
        
        assert len(response.results) == 0
