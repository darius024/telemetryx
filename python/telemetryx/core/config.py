"""Configuration management using Pydantic Settings.

Environment variables are automatically loaded and validated.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server configuration
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051

    # Environment
    python_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = ""

    # Redis
    redis_url: str = ""

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.python_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.python_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
