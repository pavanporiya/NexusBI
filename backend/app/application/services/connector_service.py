"""Application service for database connector management."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.connectors import ColumnMetadata, ConnectorConfig
from app.infrastructure.connectors import ConnectorRegistry


@dataclass(frozen=True, slots=True)
class ConnectorDiscoveryResult:
    """Represents metadata discovered from a connector."""

    schemas: list[str]
    tables: list[str]
    columns: list[ColumnMetadata]


class ConnectorService:
    """Application service for database connector operations."""

    def test_connection(self, config: ConnectorConfig) -> bool:
        """Test a connector configuration by opening a connection."""
        connector = ConnectorRegistry.create(config)
        try:
            return connector.test_connection()
        finally:
            try:
                connector.disconnect()
            except Exception:
                pass

    def discover(
        self,
        config: ConnectorConfig,
        schema: str | None = None,
        table_name: str | None = None,
    ) -> ConnectorDiscoveryResult:
        """
        Discover connector metadata for schemas, tables,
        and optionally table columns.
        """
        connector = ConnectorRegistry.create(config)
        try:
            connector.connect()

            schemas = list(connector.list_schemas())
            tables = list(connector.list_tables(schema))

            columns: list[ColumnMetadata] = []
            if table_name:
                columns = list(connector.list_columns(table_name, schema))

            return ConnectorDiscoveryResult(
                schemas=schemas,
                tables=tables,
                columns=columns,
            )
        finally:
            connector.disconnect()

    def list_schemas(self, config: ConnectorConfig) -> list[str]:
        """List schemas exposed by the connector."""
        connector = ConnectorRegistry.create(config)
        try:
            connector.connect()
            return list(connector.list_schemas())
        finally:
            connector.disconnect()

    def list_tables(
        self,
        config: ConnectorConfig,
        schema: str | None = None,
    ) -> list[str]:
        """List tables optionally scoped to a schema."""
        connector = ConnectorRegistry.create(config)
        try:
            connector.connect()
            return list(connector.list_tables(schema))
        finally:
            connector.disconnect()

    def list_columns(
        self,
        config: ConnectorConfig,
        table_name: str,
        schema: str | None = None,
    ) -> list[ColumnMetadata]:
        """List column metadata for a specific table."""
        connector = ConnectorRegistry.create(config)
        try:
            connector.connect()
            return list(connector.list_columns(table_name, schema))
        finally:
            connector.disconnect()
