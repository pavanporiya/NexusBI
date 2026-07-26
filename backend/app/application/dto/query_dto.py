"""Data Transfer Objects for Universal Query Engine API operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidateQueryRequestDTO(BaseModel):
    """Payload for validating SQL query safety and syntax."""

    sql: str = Field(..., description="Raw SQL query string to validate.")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Named parameters dictionary.",
    )


class ValidateQueryResponseDTO(BaseModel):
    """Response returned when SQL validation succeeds."""

    valid: bool = Field(default=True, description="Whether the query is valid.")
    message: str = Field(
        default="Query is valid and passed security checks.",
        description="Validation outcome message.",
    )


class ExecuteQueryRequestDTO(BaseModel):
    """Payload for executing a SQL query."""

    sql: str = Field(..., description="Raw SQL query string to execute.")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Named parameters dictionary.",
    )
    page: int | None = Field(default=None, ge=1, description="Page number (1-based).")
    page_size: int | None = Field(
        default=None, ge=1, le=1000, description="Items per page."
    )
    limit: int | None = Field(
        default=None, ge=1, description="Explicit row limit count."
    )
    offset: int | None = Field(
        default=None, ge=0, description="Explicit row offset count."
    )
    timeout: float | None = Field(
        default=None, gt=0, description="Query execution timeout in seconds."
    )


class ExplainQueryRequestDTO(BaseModel):
    """Payload for generating query plan metadata."""

    sql: str = Field(..., description="Raw SQL query string to explain.")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Named parameters dictionary.",
    )


class QueryColumnDTO(BaseModel):
    """Representation of column metadata."""

    name: str = Field(..., description="Column identifier name.")
    type: str = Field(..., description="Data type representation.")


class QueryStatisticsDTO(BaseModel):
    """Execution performance statistics."""

    query_plan: str | None = Field(
        default=None, description="Formatted execution plan string."
    )
    rows_scanned: int | None = Field(
        default=None, description="Total rows scanned in data engine."
    )
    bytes_processed: int | None = Field(
        default=None, description="Total bytes processed."
    )
    cache_hit: bool = Field(
        default=False, description="Whether result was served from cache."
    )


class QueryMetadataDTO(BaseModel):
    """Execution metadata envelope."""

    statistics: QueryStatisticsDTO = Field(..., description="Execution statistics.")
    execution_time: float = Field(..., description="Total execution time in seconds.")
    row_count: int = Field(..., description="Total result row count.")
    columns: list[QueryColumnDTO] = Field(
        ..., description="List of schema column definitions."
    )
    truncated: bool = Field(
        default=False, description="Whether rows were truncated by limits."
    )
    limit: int | None = Field(default=None, description="Applied row limit.")
    offset: int | None = Field(default=None, description="Applied row offset.")


class QueryResultDTO(BaseModel):
    """Full tabular query execution result."""

    rows: list[dict[str, Any]] = Field(..., description="Tabular dataset row objects.")
    columns: list[QueryColumnDTO] = Field(..., description="Column schema definitions.")
    column_types: dict[str, str] = Field(
        ..., description="Map of column name to data type."
    )
    execution_time: float = Field(
        ..., description="Total execution duration in seconds."
    )
    row_count: int = Field(..., description="Count of returned rows.")
    metadata: QueryMetadataDTO = Field(..., description="Query execution metadata.")
