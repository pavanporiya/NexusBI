"""Unit tests for Universal Data Connector Framework domain abstractions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from inspect import isabstract
from typing import get_type_hints

import pytest

from app.domain.connectors import (
    AuthenticationFailedError,
    ConnectionFailedError,
    ConnectorConfig,
    ConnectorError,
    ConnectorType,
    DatabaseConnector,
    MetadataDiscoveryError,
    QueryExecutionError,
    UnsupportedConnectorError,
)


def test_connector_type_values() -> None:
    """Connector types expose all supported technologies as strings."""
    assert {member.value for member in ConnectorType} == {
        "postgresql",
        "mysql",
        "sqlite",
        "sqlserver",
        "snowflake",
        "bigquery",
        "duckdb",
    }
    assert isinstance(ConnectorType.POSTGRESQL, str)


def test_connector_config_accepts_valid_configuration() -> None:
    """A complete relational connector configuration is normalized."""
    config = ConnectorConfig(
        id=" connector-1 ",
        name=" Analytics warehouse ",
        connector_type=ConnectorType.POSTGRESQL,
        host=" db.internal ",
        port=5432,
        database=" analytics ",
        username=" analyst ",
        password=" secret ",
        schema=" public ",
        ssl_enabled=True,
        extra_options={"connect_timeout": 10},
    )

    assert config.id == "connector-1"
    assert config.name == "Analytics warehouse"
    assert config.host == "db.internal"
    assert config.extra_options == {"connect_timeout": 10}


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("id", ""),
        ("name", " "),
        ("host", ""),
        ("database", " "),
        ("username", ""),
        ("password", " "),
        ("schema", ""),
        ("warehouse", " "),
        ("account", ""),
    ],
)
def test_connector_config_rejects_empty_string_values(
    field_name: str, value: object
) -> None:
    """Provided textual configuration values must be non-empty strings."""
    values: dict[str, object] = {
        "id": "connector-1",
        "name": "Warehouse",
        "connector_type": ConnectorType.SNOWFLAKE,
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        ConnectorConfig(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("port", [0, 65536, True, "5432"])
def test_connector_config_rejects_invalid_port(port: object) -> None:
    """Ports must be integer TCP port numbers."""
    with pytest.raises(ValueError, match="port"):
        ConnectorConfig(
            id="connector-1",
            name="Warehouse",
            connector_type=ConnectorType.POSTGRESQL,
            port=port,  # type: ignore[arg-type]
        )


def test_connector_config_rejects_invalid_connector_type_and_options() -> None:
    """Connector type and extra option shape are runtime-validated."""
    with pytest.raises(ValueError, match="connector_type"):
        ConnectorConfig(
            id="connector-1",
            name="Warehouse",
            connector_type="postgresql",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="extra_options"):
        ConnectorConfig(
            id="connector-1",
            name="Warehouse",
            connector_type=ConnectorType.POSTGRESQL,
            extra_options={"": "value"},
        )


def test_connector_config_is_deeply_immutable_for_its_options() -> None:
    """Frozen configuration cannot be reassigned and exposes read-only options."""
    source_options = {"features": ["read"]}
    config = ConnectorConfig(
        id="connector-1",
        name="Warehouse",
        connector_type=ConnectorType.DUCKDB,
        extra_options=source_options,
    )
    source_options["features"].append("write")

    with pytest.raises(FrozenInstanceError):
        config.name = "Renamed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        config.extra_options["read_only"] = False  # type: ignore[index]
    assert config.extra_options["features"] == ("read",)


def test_connector_exception_hierarchy() -> None:
    """Connector exceptions retain distinct, catchable domain semantics."""
    assert isinstance(AuthenticationFailedError(), ConnectionFailedError)
    assert isinstance(ConnectionFailedError(), ConnectorError)
    assert isinstance(UnsupportedConnectorError(), ConnectorError)
    assert isinstance(QueryExecutionError(), ConnectorError)
    assert isinstance(MetadataDiscoveryError(), ConnectorError)


def test_database_connector_is_abstract_and_declares_all_operations() -> None:
    """The connector port defines the full lifecycle, query, and metadata surface."""
    assert isabstract(DatabaseConnector)
    assert DatabaseConnector.__abstractmethods__ == {
        "connect",
        "disconnect",
        "test_connection",
        "execute",
        "begin_transaction",
        "commit",
        "rollback",
        "list_schemas",
        "list_tables",
        "list_views",
        "list_columns",
        "list_primary_keys",
        "list_foreign_keys",
    }
    assert get_type_hints(DatabaseConnector.execute)["return"] is not None
