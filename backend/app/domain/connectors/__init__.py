"""Universal Data Connector Framework domain abstractions."""

from app.domain.connectors.config import ConnectorConfig
from app.domain.connectors.exceptions import (
    AuthenticationFailedError,
    ConnectionFailedError,
    ConnectorError,
    MetadataDiscoveryError,
    QueryExecutionError,
    UnsupportedConnectorError,
)
from app.domain.connectors.interface import DatabaseConnector
from app.domain.connectors.types import ConnectorType

__all__ = [
    "AuthenticationFailedError",
    "ConnectionFailedError",
    "ConnectorConfig",
    "ConnectorError",
    "ConnectorType",
    "DatabaseConnector",
    "MetadataDiscoveryError",
    "QueryExecutionError",
    "UnsupportedConnectorError",
]
