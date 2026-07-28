"""Domain port for database connector implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence


class DatabaseConnector(ABC):
    """Technology-neutral contract for database connectivity and discovery."""

    @abstractmethod
    def connect(self) -> None:
        """Open a connection to the configured data source."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the active connection, if any."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Test whether the configured data source can be reached."""

    @abstractmethod
    def execute(
        self, query: str, parameters: Mapping[str, object] | None = None
    ) -> Sequence[Mapping[str, object]]:
        """Execute a query and return its result rows."""

    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a database transaction."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the active transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Roll back the active transaction."""

    @abstractmethod
    def list_schemas(self) -> Sequence[str]:
        """List schemas exposed by the configured data source."""

    @abstractmethod
    def list_tables(self, schema: str | None = None) -> Sequence[str]:
        """List tables, optionally restricted to one schema."""

    @abstractmethod
    def list_views(self, schema: str | None = None) -> Sequence[str]:
        """List views, optionally restricted to one schema."""

    @abstractmethod
    def list_columns(
        self, table_name: str, schema: str | None = None
    ) -> Sequence[Mapping[str, object]]:
        """List column metadata for a table or view."""
