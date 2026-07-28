"""Connector registry for managing database connector instances."""

from __future__ import annotations

import logging

from app.domain.connectors import (
    ConnectorConfig,
    ConnectorType,
    DatabaseConnector,
    UnsupportedConnectorError,
)
from app.infrastructure.connectors.postgres import PostgresConnector

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Factory and registry for creating and managing database connectors.

    Implements the Factory pattern to provide connector instances based
    on ConnectorType. Supports registration of custom connector implementations.

    Usage:
        registry = ConnectorRegistry()
        config = ConnectorConfig(
            id="prod_postgres",
            name="Production Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="db.example.com",
            port=5432,
            database="prod_db",
            username="user",
            password="pass"
        )
        connector = registry.create(config)
        connector.connect()
    """

    # Mapping of ConnectorType to connector class
    _connectors: dict[ConnectorType, type[DatabaseConnector]] = {
        ConnectorType.POSTGRESQL: PostgresConnector,
    }

    @classmethod
    def register(
        cls, connector_type: ConnectorType, connector_class: type[DatabaseConnector]
    ) -> None:
        """Register a custom connector implementation.

        Args:
            connector_type: The ConnectorType this implementation handles
            connector_class: The DatabaseConnector subclass to register

        Raises:
            TypeError: If connector_class doesn't inherit DatabaseConnector
        """
        if not issubclass(connector_class, DatabaseConnector):
            raise TypeError(
                f"{connector_class.__name__} must inherit from DatabaseConnector"
            )

        cls._connectors[connector_type] = connector_class
        logger.info(
            f"Registered connector {connector_class.__name__} for {connector_type}"
        )

    @classmethod
    def create(self, config: ConnectorConfig) -> DatabaseConnector:
        """Create a connector instance for the specified configuration.

        Args:
            config: ConnectorConfig with connection parameters

        Returns:
            Concrete DatabaseConnector subclass instance

        Raises:
            UnsupportedConnectorError: If no implementation exists for the type
            ValueError: If connector initialization fails
        """
        connector_type = config.connector_type

        if connector_type not in self._connectors:
            raise UnsupportedConnectorError(
                f"No connector implementation found for {connector_type}. "
                f"Supported types: {list(self._connectors.keys())}"
            )

        connector_class = self._connectors[connector_type]
        logger.info(
            f"Creating {connector_class.__name__} for config "
            f"{config.id} ({config.name})"
        )

        return connector_class(config)  # type: ignore[call-arg]

    @classmethod
    def list_supported(cls) -> list[ConnectorType]:
        """List all supported connector types.

        Returns:
            List of registered ConnectorType values
        """
        return list(cls._connectors.keys())

    @classmethod
    def is_supported(cls, connector_type: ConnectorType) -> bool:
        """Check if a connector type is supported.

        Args:
            connector_type: The ConnectorType to check

        Returns:
            True if supported, False otherwise
        """
        return connector_type in cls._connectors
