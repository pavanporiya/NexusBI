"""Domain exceptions raised by database connector implementations."""

from __future__ import annotations


class ConnectorError(Exception):
    """Base exception for all connector-related failures."""


class ConnectionFailedError(ConnectorError):
    """Raised when a connection to a data source cannot be established."""


class AuthenticationFailedError(ConnectionFailedError):
    """Raised when a data source rejects the supplied credentials."""


class UnsupportedConnectorError(ConnectorError):
    """Raised when no implementation supports a connector type."""


class QueryExecutionError(ConnectorError):
    """Raised when a connector cannot execute a query."""


class MetadataDiscoveryError(ConnectorError):
    """Raised when schemas, objects, or columns cannot be discovered."""
