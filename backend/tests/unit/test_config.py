"""Tests for the Configuration System.

Verifies Settings model validation, environment-specific loading,
secret handling, and configuration provider caching.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr


class TestSettingsDefaults:
    """Tests for default configuration values."""

    def test_project_name_default(self, test_settings) -> None:
        assert test_settings.PROJECT_NAME == "NexusBI Backend"

    def test_api_prefix_default(self, test_settings) -> None:
        assert test_settings.API_V1_STR == "/api/v1"

    def test_version_default(self, test_settings) -> None:
        assert test_settings.VERSION == "1.0.0"

    def test_max_query_row_limit(self, test_settings) -> None:
        assert test_settings.MAX_QUERY_ROW_LIMIT == 50_000

    def test_max_query_text_length(self, test_settings) -> None:
        assert test_settings.MAX_QUERY_TEXT_LENGTH == 2_000


class TestSettingsValidation:
    """Tests for configuration validation rules."""

    def test_environment_normalised_to_lowercase(self) -> None:
        from app.core.config import Settings

        with patch.dict(os.environ, {"ENV": "DEVELOPMENT"}, clear=False):
            s = Settings(
                ENV="DEVELOPMENT",  # type: ignore[arg-type]
                SECRET_KEY=SecretStr("test"),
            )
            assert s.ENV.value == "development"

    def test_log_level_normalised_to_uppercase(self) -> None:
        from app.core.config import Settings

        s = Settings(
            LOG_LEVEL="debug",  # type: ignore[arg-type]
            SECRET_KEY=SecretStr("test"),
        )
        assert s.LOG_LEVEL.value == "DEBUG"

    def test_invalid_port_raises_error(self) -> None:
        from pydantic import ValidationError

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                PORT=99999,
                SECRET_KEY=SecretStr("test"),
            )

    def test_negative_token_expiry_raises_error(self) -> None:
        from pydantic import ValidationError

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                ACCESS_TOKEN_EXPIRE_MINUTES=-1,
                SECRET_KEY=SecretStr("test"),
            )


class TestSettingsProperties:
    """Tests for computed properties."""

    def test_postgres_dsn_format(self, test_settings) -> None:
        dsn = test_settings.postgres_dsn
        assert dsn.startswith("postgresql+psycopg2://")
        assert test_settings.POSTGRES_DB in dsn

    def test_redis_url_format(self, test_settings) -> None:
        url = test_settings.redis_url
        assert url.startswith("redis://")

    def test_is_development_property(self) -> None:
        from app.core.config import Settings

        s = Settings(ENV="development", SECRET_KEY=SecretStr("test"))  # type: ignore[arg-type]
        assert s.is_development is True

    def test_is_testing_property(self) -> None:
        from app.core.config import Settings

        s = Settings(ENV="testing", SECRET_KEY=SecretStr("test"))  # type: ignore[arg-type]
        assert s.is_testing is True

    def test_is_production_property(self) -> None:
        from app.core.config import Settings

        s = Settings(ENV="production", SECRET_KEY=SecretStr("secure_key"))  # type: ignore[arg-type]
        assert s.is_production is True


class TestSecretHandling:
    """Tests for sensitive value handling."""

    def test_secret_key_is_secret_str(self, test_settings) -> None:
        assert isinstance(test_settings.SECRET_KEY, SecretStr)

    def test_postgres_password_is_secret_str(self, test_settings) -> None:
        assert isinstance(test_settings.POSTGRES_PASSWORD, SecretStr)

    def test_secret_str_repr_is_masked(self, test_settings) -> None:
        repr_str = repr(test_settings.SECRET_KEY)
        assert "**********" in repr_str

    def test_secret_value_accessible(self, test_settings) -> None:
        value = test_settings.SECRET_KEY.get_secret_value()
        assert isinstance(value, str)
        assert len(value) > 0


class TestConfigurationProvider:
    """Tests for the get_settings() provider function."""

    def test_returns_settings_instance(self) -> None:
        from app.core.config import Settings, get_settings

        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)
        get_settings.cache_clear()

    def test_cached_singleton(self) -> None:
        from app.core.config import get_settings

        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()
