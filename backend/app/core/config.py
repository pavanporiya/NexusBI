"""NexusBI Configuration System.

Provides a layered settings model with environment-specific overrides,
secret loading support, and runtime validation. All configuration is
sourced from environment variables via Pydantic Settings, following the
12-Factor App methodology.

Architecture Reference: phase2_1_repository_blueprint.md Section 5
"""

from __future__ import annotations

import logging
import os
import secrets
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT.parent / "config"
ENV_DIR = CONFIG_DIR / "envs"


class Environment(StrEnum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Base Settings
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    """Central configuration broker for the NexusBI backend service.

    Settings are loaded in order of precedence:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values (lowest priority)

    Secrets (SECRET_KEY, POSTGRES_PASSWORD, API keys) are stored as
    SecretStr to prevent accidental logging of sensitive values.
    """

    # ── Application ────────────────────────────────────────────────────
    PROJECT_NAME: str = "NexusBI Backend"
    API_V1_STR: str = "/api/v1"
    ENV: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: LogLevel = LogLevel.INFO
    VERSION: str = "1.0.0"

    # ── Server ─────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False

    # ── CORS ───────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # ── Security ───────────────────────────────────────────────────────
    SECRET_KEY: SecretStr = SecretStr(secrets.token_hex(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "RS256"

    # ── PostgreSQL Metadata Database ───────────────────────────────────
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr = SecretStr("postgres")
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nexusbi_metadata"
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20
    POSTGRES_POOL_TIMEOUT: int = 30
    POSTGRES_ECHO: bool = False

    @property
    def postgres_dsn(self) -> str:
        """Build the PostgreSQL connection DSN."""
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_postgres_dsn(self) -> str:
        """Build the async PostgreSQL connection DSN."""
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ──────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: SecretStr = SecretStr("")

    @property
    def redis_url(self) -> str:
        """Build the Redis connection URL."""
        password = self.REDIS_PASSWORD.get_secret_value()
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── Snowflake Analytics DW ─────────────────────────────────────────
    SNOWFLAKE_ACCOUNT: str = ""
    SNOWFLAKE_USER: str = ""
    SNOWFLAKE_PASSWORD: SecretStr = SecretStr("")
    SNOWFLAKE_DATABASE: str = ""
    SNOWFLAKE_SCHEMA: str = ""
    SNOWFLAKE_WAREHOUSE: str = ""
    SNOWFLAKE_ROLE: str = ""
    SNOWFLAKE_QUERY_TIMEOUT: int = 30

    # ── AI Model Configuration ─────────────────────────────────────────
    ANTHROPIC_API_KEY: SecretStr = SecretStr("")
    OPENAI_API_KEY: SecretStr = SecretStr("")
    LLM_PRIMARY_MODEL: str = "claude-sonnet-4-20250514"
    LLM_FALLBACK_MODEL: str = "gpt-4o"
    LLM_REQUEST_TIMEOUT: int = 15
    LLM_MAX_RETRIES: int = 2

    # ── Feature Flags ──────────────────────────────────────────────────
    ENABLE_SEMANTIC_CACHE: bool = False
    ENABLE_FORECASTING: bool = True
    ENABLE_AUDIT_LOGGING: bool = True

    # ── Rate Limiting ──────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_CHAT_MESSAGES_PER_MINUTE: int = 30

    # ── Query Guardrails ───────────────────────────────────────────────
    MAX_QUERY_ROW_LIMIT: int = 50_000
    MAX_QUERY_TEXT_LENGTH: int = 2_000

    # ── Observability ──────────────────────────────────────────────────
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_METRICS: bool = False

    # ── Pydantic Settings Configuration ────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Validators ─────────────────────────────────────────────────────

    @field_validator("ENV", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> str:
        """Normalise environment string to lowercase."""
        if isinstance(v, str):
            v = v.strip().lower()
        return v

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: Any) -> str:
        """Normalise log level string to uppercase."""
        if isinstance(v, str):
            v = v.strip().upper()
        return v

    @field_validator("POSTGRES_PORT", "REDIS_PORT", "PORT", mode="before")
    @classmethod
    def validate_port(cls, v: Any) -> int:
        """Ensure port values are within valid range."""
        port = int(v)
        if not 1 <= port <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {port}")
        return port

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES", mode="before")
    @classmethod
    def validate_token_expiry(cls, v: Any) -> int:
        """Ensure token expiry is positive."""
        val = int(v)
        if val < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be >= 1")
        return val

    @model_validator(mode="after")
    def validate_production_secrets(self) -> Settings:
        """Enforce that production and staging environments have real secrets."""
        if self.ENV in (Environment.PRODUCTION, Environment.STAGING):
            secret_value = self.SECRET_KEY.get_secret_value()
            if secret_value == "placeholder_secret_key_change_in_production":
                raise ValueError(
                    "SECRET_KEY must be set to a secure value in "
                    f"{self.ENV} environment"
                )
        return self

    @model_validator(mode="after")
    def set_debug_defaults(self) -> Settings:
        """Auto-configure debug-related settings by environment."""
        if self.ENV == Environment.DEVELOPMENT:
            object.__setattr__(self, "DEBUG", True)
            object.__setattr__(self, "POSTGRES_ECHO", False)
            object.__setattr__(self, "RELOAD", True)
        elif self.ENV == Environment.PRODUCTION:
            object.__setattr__(self, "DEBUG", False)
            object.__setattr__(self, "RELOAD", False)
        return self

    # ── Properties ─────────────────────────────────────────────────────

    @property
    def is_development(self) -> bool:
        return self.ENV == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.ENV == Environment.TESTING

    @property
    def is_production(self) -> bool:
        return self.ENV == Environment.PRODUCTION

    @property
    def python_log_level(self) -> int:
        """Return the stdlib logging level integer."""
        return getattr(logging, self.LOG_LEVEL.value, logging.INFO)


# ---------------------------------------------------------------------------
# Configuration Provider
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance.

    The env_file is resolved from the ENV environment variable:
    - development → config/envs/.env.development (if exists)
    - testing     → config/envs/.env.testing
    - staging     → config/envs/.env.staging
    - production  → (relies on injected environment variables only)

    Falls back to the root .env file if no environment-specific file exists.
    """
    env = os.getenv("ENV", "development").strip().lower()

    env_file: str | Path = ".env"
    env_specific = ENV_DIR / f".env.{env}"
    if env_specific.is_file():
        env_file = env_specific

    return Settings(_env_file=env_file)  # type: ignore[call-arg]


# Module-level singleton for backward compatibility
settings = get_settings()
