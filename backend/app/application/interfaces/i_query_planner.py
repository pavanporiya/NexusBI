"""Interface for query planning port."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.query import QueryMetadata, QueryRequest


class IQueryPlanner(ABC):
    """Port interface for generating query execution plans and metadata."""

    @abstractmethod
    def plan(self, request: QueryRequest) -> QueryMetadata:
        """Generate execution plan metadata for a query request.

        Raises:
            InvalidQueryError: If the query fails syntax or planning analysis.
        """
