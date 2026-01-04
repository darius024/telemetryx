"""Async gRPC server with lifecycle management.

This module provides the main server class that handles:
- Server startup and binding
- Graceful shutdown on SIGTERM/SIGINT
- Health check service registration
"""

import asyncio
import signal
from concurrent import futures
from typing import Any

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from python.telemetryx.grpc_server.handlers import AnalyticsServiceHandler, RulesServiceHandler
from python.telemetryx.grpc_server.interceptors import LoggingInterceptor
from telemetryx.core import Settings, get_logger, setup_logging, get_settings

# Import generated proto services (we'll register handlers later)
from telemetryx.proto import rules_pb2, analytics_pb2
from telemetryx.proto import rules_pb2_grpc, analytics_pb2_grpc


class GrpcServer:
    """Async gRPC server for TelemetryX Python Brain.
    
    Handles server lifecycle including graceful shutdown.
    
    Example:
        server = GrpcServer()
        await server.start()
        await server.wait_for_termination()
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the server."""
        self._settings = settings or get_settings()
        self._server: grpc.aio.Server | None = None
        self._logger = get_logger(__name__, component="grpc-server")
        self._shutdown_event = asyncio.Event()

    @property
    def address(self) -> str:
        """Get the server bind address."""
        return f"{self._settings.grpc_host}:{self._settings.grpc_port}"

    async def start(self) -> None:
        """Start the gRPC server.

        Binds to the configured host:port and registers all services.
        """
        # Create the async server
        self._server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            interceptors=[LoggingInterceptor()],
            options=[
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ],
        )

        # Register health check service
        health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self._server)

        # Set initial health status
        health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
        health_servicer.set(
            "telemetryx.RulesService", health_pb2.HealthCheckResponse.SERVING
        )
        health_servicer.set(
            "telemetryx.AnalyticsService", health_pb2.HealthCheckResponse.SERVING
        )

        # Register service handlers
        rules_pb2_grpc.add_RulesServiceServicer_to_server(
            RulesServiceHandler(), self._server
        )
        analytics_pb2_grpc.add_AnalyticsServiceServicer_to_server(
            AnalyticsServiceHandler(), self._server
        )

        # Enable reflection for debugging with grpcurl
        service_names = (
            rules_pb2.DESCRIPTOR.services_by_name["RulesService"].full_name,
            analytics_pb2.DESCRIPTOR.services_by_name["AnalyticsService"].full_name,
            reflection.SERVICE_NAME,
            health.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, self._server)

        # Bind to address
        self._server.add_insecure_port(self.address)

        # Start serving
        await self._server.start()
        self._logger.info(
            "gRPC server started",
            address=self.address,
            services=list(service_names),
        )

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_signal(s)),
            )

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        self._logger.info("Received shutdown signal", signal=sig.name)
        await self.stop()

    async def stop(self, grace_period: float = 5.0) -> None:
        """Stop the server gracefully."""
        if self._server is None:
            return

        self._logger.info("Initiating graceful shutdown", grace_period=grace_period)

        # Stop accepting new requests and wait for existing ones
        await self._server.stop(grace_period)

        self._logger.info("gRPC server stopped")
        self._shutdown_event.set()

    async def wait_for_termination(self) -> None:
        """Block until the server is terminated.

        Use this to keep the main coroutine alive.
        """
        await self._shutdown_event.wait()


async def serve() -> None:
    """Main entry point for running the gRPC server.

    This function:
    1. Sets up logging
    2. Creates and starts the server
    3. Waits for termination signal
    """
    # Initialize logging
    setup_logging()

    logger = get_logger(__name__)
    settings = get_settings()

    logger.info(
        "Starting TelemetryX Python Brain",
        environment=settings.python_env,
        log_level=settings.log_level,
    )

    # Create and start server
    server = GrpcServer(settings)

    try:
        await server.start()
        await server.wait_for_termination()
    except Exception as e:
        logger.exception("Server error", error=str(e))
        raise
    finally:
        logger.info("Server shutdown complete")
