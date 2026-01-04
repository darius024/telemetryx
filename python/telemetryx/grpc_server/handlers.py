"""gRPC service handler implementations.

These classes implement the RPC methods defined in the proto files.
"""

import time

import grpc

from telemetryx.core import get_logger
from telemetryx.proto import analytics_pb2, common_pb2, rules_pb2
from telemetryx.proto.analytics_pb2_grpc import AnalyticsServiceServicer
from telemetryx.proto.rules_pb2_grpc import RulesServiceServicer


class RulesServiceHandler(RulesServiceServicer):
    """Handler for RulesService RPCs.

    Implements rule evaluation against incoming events.
    """

    def __init__(self) -> None:
        self._logger = get_logger(__name__, service="RulesService")

    async def EvaluateEvent(
        self,
        request: rules_pb2.EvaluateRequest,
        context: grpc.aio.ServicerContext,
    ) -> rules_pb2.EvaluateResponse:
        """Evaluate an event against all active rules."""
        start_time = time.perf_counter()

        event = request.event
        self._logger.info(
            "Evaluating event",
            event_id=event.id,
            event_type=event.event_type,
        )

        # TODO: Implement actual rule evaluation
        # For now, return empty matches
        matches: list[rules_pb2.RuleMatch] = []

        # Example: Add a dummy match for testing
        if event.event_type == "error":
            match = rules_pb2.RuleMatch(
                rule_id="rule-001",
                rule_name="Error Event Alert",
                severity=rules_pb2.WARNING,
                actions=[
                    rules_pb2.Action(
                        action_type="log",
                        config='{"level": "warning"}',
                    )
                ],
            )
            matches.append(match)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        self._logger.info(
            "Evaluation complete",
            event_id=event.id,
            matches_count=len(matches),
            elapsed_ms=elapsed_ms,
        )

        return rules_pb2.EvaluateResponse(
            matches=matches,
            evaluation_time_ms=elapsed_ms,
        )

    async def HealthCheck(
        self,
        request: common_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.HealthCheckResponse:
        """Health check for RulesService."""
        return common_pb2.HealthCheckResponse(
            status=common_pb2.HealthCheckResponse.SERVING,
        )


class AnalyticsServiceHandler(AnalyticsServiceServicer):
    """Handler for AnalyticsService RPCs.

    Implements anomaly detection on event batches.
    """

    def __init__(self) -> None:
        self._logger = get_logger(__name__, service="AnalyticsService")

    async def DetectAnomalies(
        self,
        request: analytics_pb2.DetectAnomaliesRequest,
        context: grpc.aio.ServicerContext,
    ) -> analytics_pb2.DetectAnomaliesResponse:
        """Detect anomalies in a batch of events."""
        start_time = time.perf_counter()

        events = request.events
        model_name = request.model_name or "default"
        sensitivity = request.sensitivity or 0.5

        self._logger.info(
            "Detecting anomalies",
            event_count=len(events),
            model=model_name,
            sensitivity=sensitivity,
        )

        # TODO: Implement actual ML inference
        # For now, return dummy results
        results: list[analytics_pb2.AnomalyResult] = []

        for event in events:
            # Placeholder: mark events with "error" type as anomalies
            is_anomaly = event.event_type == "error"
            score = 0.9 if is_anomaly else 0.1

            result = analytics_pb2.AnomalyResult(
                event_id=event.id,
                is_anomaly=is_anomaly,
                anomaly_score=score,
                explanation="Placeholder detection" if is_anomaly else "",
            )
            results.append(result)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        anomaly_count = sum(1 for r in results if r.is_anomaly)
        self._logger.info(
            "Detection complete",
            event_count=len(events),
            anomaly_count=anomaly_count,
            elapsed_ms=elapsed_ms,
        )

        return analytics_pb2.DetectAnomaliesResponse(
            results=results,
            inference_time_ms=elapsed_ms,
        )

    async def HealthCheck(
        self,
        request: common_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext,
    ) -> common_pb2.HealthCheckResponse:
        """Health check for AnalyticsService."""
        return common_pb2.HealthCheckResponse(
            status=common_pb2.HealthCheckResponse.SERVING,
        )
