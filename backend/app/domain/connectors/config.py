"""Framework-independent configuration value object for data connectors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from app.domain.connectors.types import ConnectorType


@dataclass(frozen=True, slots=True)
class ConnectorConfig:
    """Immutable connection settings supplied to a database connector."""

    id: str
    name: str
    connector_type: ConnectorType
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    schema: str | None = None
    warehouse: str | None = None
    account: str | None = None
    ssl_enabled: bool = False
    extra_options: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize connector configuration values."""
        object.__setattr__(self, "id", self._validate_required("id", self.id))
        object.__setattr__(self, "name", self._validate_required("name", self.name))

        if not isinstance(self.connector_type, ConnectorType):
            raise ValueError("connector_type must be a ConnectorType.")
        if isinstance(self.port, bool) or (
            self.port is not None and not isinstance(self.port, int)
        ):
            raise ValueError("port must be an integer when provided.")
        if self.port is not None and not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535.")
        if not isinstance(self.ssl_enabled, bool):
            raise ValueError("ssl_enabled must be a boolean.")
        if not isinstance(self.extra_options, Mapping):
            raise ValueError("extra_options must be a mapping.")

        for field_name in (
            "host",
            "database",
            "username",
            "password",
            "schema",
            "warehouse",
            "account",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self, field_name, self._validate_required(field_name, value)
                )

        options = dict(self.extra_options)
        if any(not isinstance(key, str) or not key.strip() for key in options):
            raise ValueError("extra_options keys must be non-empty strings.")
        object.__setattr__(
            self,
            "extra_options",
            MappingProxyType(
                {
                    key: self._freeze_option_value(value)
                    for key, value in options.items()
                }
            ),
        )

    @staticmethod
    def _validate_required(field_name: str, value: object) -> str:
        """Return a normalized non-empty string field value."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string.")
        return value.strip()

    @classmethod
    def _freeze_option_value(cls, value: object) -> object:
        """Recursively freeze mutable option containers."""
        if isinstance(value, Mapping):
            return MappingProxyType(
                {key: cls._freeze_option_value(item) for key, item in value.items()}
            )
        if isinstance(value, list):
            return tuple(cls._freeze_option_value(item) for item in value)
        if isinstance(value, set):
            return frozenset(cls._freeze_option_value(item) for item in value)
        if isinstance(value, tuple):
            return tuple(cls._freeze_option_value(item) for item in value)
        return value
