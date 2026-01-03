"""Custom exception hierarchy for TelemetryX.

All application exceptions inherit from TelemetryXError for easy catching.
"""

from typing import Any


class TelemetryXError(Exception):
    """Base exception for all TelemetryX errors.
    
    Attributes:
        message: Human-readable error message
        details: Optional dictionary with additional context
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | {self.details}"
        return self.message


class ConfigurationError(TelemetryXError):
    """Raised when configuration is invalid or missing."""
    pass


class ServiceError(TelemetryXError):
    """Raised when a service operation fails."""
    pass


class RuleEvaluationError(ServiceError):
    """Raised when rule evaluation fails."""
    pass


class AnomalyDetectionError(ServiceError):
    """Raised when anomaly detection fails."""
    pass


class DatabaseError(TelemetryXError):
    """Raised when database operations fail."""
    pass


class ConnectionError(TelemetryXError):
    """Raised when connection to external service fails."""
    pass
