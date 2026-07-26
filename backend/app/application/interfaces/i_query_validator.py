"""Interface for query validation port."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.query import QueryRequest


class IQueryValidator(ABC):
    """Port interface for validating query security, syntax, and parameters."""

    @abstractmethod
    def validate(self, request: QueryRequest) -> None:
        """Validate the given query request.

        Raises:
            InvalidQueryError: If the query fails AST, security, or syntax checks.
        """
