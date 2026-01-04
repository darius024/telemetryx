"""Shared pytest fixtures for TelemetryX tests."""

import pytest

from telemetryx.core import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings with defaults."""
    return Settings(
        grpc_host="127.0.0.1",
        grpc_port=50051,
        python_env="test",
        log_level="DEBUG",
    )


@pytest.fixture
def sample_event_data() -> dict:
    """Sample event data for testing."""
    return {
        "id": "evt-123",
        "event_type": "page_view",
        "timestamp": 1704307200000,
        "source": "web-frontend",
        "attributes": {"page": "/home", "user_id": "user-456"},
        "value": 1.0,
    }


@pytest.fixture
def sample_error_event_data() -> dict:
    """Sample error event for testing rule matching."""
    return {
        "id": "evt-error-789",
        "event_type": "error",
        "timestamp": 1704307200000,
        "source": "api-server",
        "attributes": {"message": "Connection timeout"},
        "value": 0.0,
    }
