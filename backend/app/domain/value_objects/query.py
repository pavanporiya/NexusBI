"""Domain value objects for the Universal Query Engine.

Framework-independent value objects representing queries, requests, columns,
statistics, metadata, and results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from app.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class Query:
    """Immutable value object encapsulating a raw SQL query string."""

    sql: str

    def __post_init__(self) -> None:
        """Validate non-empty SQL string."""
        if not self.sql or not self.sql.strip():
            raise DomainValidationError("Query SQL string must not be empty.")
        object.__setattr__(self, "sql", self.sql.strip())

    def __str__(self) -> str:
        return self.sql


@dataclass(frozen=True, slots=True)
class QueryColumn:
    """Value object representing result column schema information."""

    name: str
    type: str

    def __post_init__(self) -> None:
        """Normalize column parameters."""
        if not self.name or not self.name.strip():
            raise DomainValidationError("QueryColumn name must not be empty.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "type", (self.type or "unknown").strip().lower())


@dataclass(frozen=True, slots=True)
class QueryStatistics:
    """Value object capturing query execution statistics."""

    query_plan: str | None = None
    rows_scanned: int | None = None
    bytes_processed: int | None = None
    cache_hit: bool = False


@dataclass(frozen=True, slots=True)
class QueryMetadata:
    """Value object encapsulating query metadata and execution diagnostics."""

    statistics: QueryStatistics = field(default_factory=QueryStatistics)
    execution_time: float = 0.0
    row_count: int = 0
    columns: list[QueryColumn] = field(default_factory=list)
    truncated: bool = False
    limit: int | None = None
    offset: int | None = None


@dataclass(frozen=True, slots=True)
class QueryRequest:
    """Value object representing a query execution request."""

    query: Query
    parameters: dict[str, Any] = field(default_factory=dict)
    page: int | None = None
    page_size: int | None = None
    limit: int | None = None
    offset: int | None = None
    timeout: float | None = None
    dataset_id: str | None = None

    @classmethod
    def create(
        cls,
        sql: str | Query,
        parameters: dict[str, Any] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        timeout: float | None = None,
        dataset_id: str | None = None,
    ) -> Self:
        """Factory constructor ensuring strongly typed Query VO."""
        query_vo = sql if isinstance(sql, Query) else Query(sql=sql)
        params = dict(parameters or {})
        return cls(
            query=query_vo,
            parameters=params,
            page=page,
            page_size=page_size,
            limit=limit,
            offset=offset,
            timeout=timeout,
            dataset_id=dataset_id,
        )

    def get_effective_limit(self) -> int | None:
        """Compute effective row limit considering pagination vs explicit limit."""
        if self.limit is not None and self.limit > 0:
            return self.limit
        if self.page_size is not None and self.page_size > 0:
            return self.page_size
        return None

    def get_effective_offset(self) -> int | None:
        """Compute effective row offset considering pagination vs explicit offset."""
        if self.offset is not None and self.offset >= 0:
            return self.offset
        if self.page is not None and self.page_size is not None:
            effective_page = max(1, self.page)
            return (effective_page - 1) * self.page_size
        return None


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Value object capturing full query execution result."""

    rows: list[dict[str, Any]]
    columns: list[QueryColumn]
    column_types: dict[str, str]
    execution_time: float
    row_count: int
    metadata: QueryMetadata
