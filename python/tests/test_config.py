"""Tests for configuration management."""

from telemetryx.core import Settings, get_settings
from telemetryx.core.config import Settings as SettingsClass


class TestSettings:
    """Tests for the Settings class."""

    def test_default_values(self) -> None:
        """Settings should have sensible defaults."""
        settings = Settings()

        assert settings.grpc_host == "0.0.0.0"
        assert settings.grpc_port == 50051
        assert settings.python_env == "development"
        assert settings.log_level == "INFO"

    def test_custom_values(self, settings: Settings) -> None:
        """Settings should accept custom values."""
        assert settings.grpc_host == "127.0.0.1"
        assert settings.python_env == "test"

    def test_is_production(self) -> None:
        """is_production should return True only for production env."""
        dev_settings = Settings(python_env="development")
        prod_settings = Settings(python_env="production")

        assert dev_settings.is_production is False
        assert prod_settings.is_production is True

    def test_is_development(self) -> None:
        """is_development should return True only for development env."""
        dev_settings = Settings(python_env="development")
        prod_settings = Settings(python_env="production")

        assert dev_settings.is_development is True
        assert prod_settings.is_development is False

    def test_optional_database_url(self) -> None:
        """database_url should be optional."""
        settings = Settings()
        assert not settings.database_url  # Empty string or None are both falsy

        settings_with_db = Settings(database_url="postgres://localhost/test")
        assert settings_with_db.database_url == "postgres://localhost/test"


class TestGetSettings:
    """Tests for the get_settings function."""

    def test_returns_settings_instance(self) -> None:
        """get_settings should return a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, SettingsClass)

    def test_caches_settings(self) -> None:
        """get_settings should return the same instance (cached)."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
