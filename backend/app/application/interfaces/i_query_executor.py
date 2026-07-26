"""Interface for query execution port."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.query import QueryRequest, QueryResult


class IQueryExecutor(ABC):
    """Port interface for executing read-only SQL queries against data engines."""

    @abstractmethod
    def execute(self, request: QueryRequest) -> QueryResult:
        """Execute a read-only query and return formatted results and metadata.

        Raises:
            InvalidQueryError: If query parameters or structure are invalid.
            QueryTimeoutError: If execution exceeds configured timeout limit.
            QueryExecutionError: If runtime database execution fails.
        """
