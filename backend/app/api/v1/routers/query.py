"""Query Engine REST API endpoints (v1 namespace).

Provides HTTP handlers for SQL query validation, execution, explanation,
and dataset preview functionality backed by the universal query service.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_current_user,
    get_query_service,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.error_dto import create_error_responses
from app.application.dto.query_dto import (
    ExecuteQueryRequestDTO,
    ExplainQueryRequestDTO,
    QueryColumnDTO,
    QueryMetadataDTO,
    QueryResultDTO,
    QueryStatisticsDTO,
    ValidateQueryRequestDTO,
    ValidateQueryResponseDTO,
)
from app.application.services.query_service import QueryService
from app.domain.entities.user import User
from app.domain.value_objects.query import QueryMetadata, QueryRequest, QueryResult

router = APIRouter(prefix="/query", tags=["Universal Query Engine"])


# ── Helpers ────────────────────────────────────────────────────────────────


def _map_result_to_dto(result: QueryResult) -> QueryResultDTO:
    """Map a QueryResult value object to its API response DTO."""
    columns = [
        QueryColumnDTO(
            name=c.name if hasattr(c, "name") else str(c),
            type=c.type if hasattr(c, "type") else "unknown",
        )
        for c in result.columns
    ]
    return QueryResultDTO(
        rows=result.rows,
        columns=columns,
        column_types=result.column_types,
        execution_time=result.execution_time,
        row_count=result.row_count,
        metadata=QueryMetadataDTO(
            statistics=QueryStatisticsDTO(),
            execution_time=result.execution_time,
            row_count=result.row_count,
            columns=columns,
        ),
    )


def _map_metadata_to_dto(meta: QueryMetadata) -> QueryMetadataDTO:
    """Map QueryMetadata to its API response DTO."""
    return QueryMetadataDTO(
        statistics=QueryStatisticsDTO(
            query_plan=meta.statistics.query_plan,
            rows_scanned=meta.statistics.rows_scanned,
            bytes_processed=meta.statistics.bytes_processed,
            cache_hit=meta.statistics.cache_hit,
        ),
        execution_time=meta.execution_time,
        row_count=meta.row_count,
        columns=[
            QueryColumnDTO(name=c.name, type=c.type)
            for c in meta.columns
        ],
        truncated=meta.truncated,
        limit=meta.limit,
        offset=meta.offset,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────

_SENSITIVE_COLUMNS = frozenset({
    "hashed_password", "password_hash", "secret", "token",
    "api_key", "private_key", "credential", "ssn",
})


@router.post(
    "/validate",
    response_model=ValidateQueryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Validate SQL Query Safety",
    operation_id="query_validate",
    response_description="Validation result with status and message.",
    responses=create_error_responses(400, 401, 403, 500),
    description=(
        "Validates a raw SQL query string for safety, syntax correctness, "
        "and read-only restrictions. Does NOT execute the query."
    ),
    dependencies=[Depends(require_permission("query:execute"))],
)
def validate_query(
    dto: ValidateQueryRequestDTO,
    _current_user: Annotated[
        User, Depends(get_current_user)
    ] = None,  # type: ignore[assignment]
    query_service: Annotated[
        QueryService, Depends(get_query_service)
    ] = None,  # type: ignore[assignment]
) -> ValidateQueryResponseDTO:
    """Validate a SQL query for safety and syntax correctness."""
    request_vo = QueryRequest.create(sql=dto.sql, parameters=dto.parameters)
    query_service.validate(request_vo)
    return ValidateQueryResponseDTO(
        valid=True,
        message="Query is valid and passed security checks.",
    )


@router.post(
    "/execute",
    response_model=QueryResultDTO,
    status_code=status.HTTP_200_OK,
    summary="Execute SQL Query",
    operation_id="query_execute",
    response_description="Query result rows, column metadata, and execution timing.",
    responses=create_error_responses(400, 401, 403, 422, 500),
    description=(
        "Validates and executes a read-only SQL SELECT query. "
        "Returns tabular rows with column metadata and execution timing."
    ),
    dependencies=[Depends(require_permission("query:execute"))],
)
def execute_query(
    dto: ExecuteQueryRequestDTO,
    _current_user: Annotated[
        User, Depends(get_current_user)
    ] = None,  # type: ignore[assignment]
    query_service: Annotated[
        QueryService, Depends(get_query_service)
    ] = None,  # type: ignore[assignment]
) -> QueryResultDTO:
    """Execute a validated read-only SQL query."""
    request_vo = QueryRequest.create(
        sql=dto.sql,
        parameters=dto.parameters,
        limit=dto.limit,
    )
    result_vo = query_service.execute(request_vo)
    return _map_result_to_dto(result_vo)


@router.post(
    "/explain",
    response_model=QueryMetadataDTO,
    status_code=status.HTTP_200_OK,
    summary="Explain SQL Query Plan",
    operation_id="query_explain",
    response_description="Query plan metadata including tables, columns, cost.",
    responses=create_error_responses(400, 401, 403, 500),
    description=(
        "Analyzes a SQL query and returns structural metadata including "
        "accessed tables, columns, estimated cost, and join/subquery indicators."
    ),
    dependencies=[Depends(require_permission("query:explain"))],
)
def explain_query(
    dto: ExplainQueryRequestDTO,
    _current_user: Annotated[
        User, Depends(get_current_user)
    ] = None,  # type: ignore[assignment]
    query_service: Annotated[
        QueryService, Depends(get_query_service)
    ] = None,  # type: ignore[assignment]
) -> QueryMetadataDTO:
    """Explain a SQL query plan."""
    request_vo = QueryRequest.create(sql=dto.sql, parameters=dto.parameters)
    meta_vo = query_service.explain(request_vo)
    return _map_metadata_to_dto(meta_vo)


@router.get(
    "/preview-dataset/{dataset_id}",
    response_model=QueryResultDTO,
    status_code=status.HTTP_200_OK,
    summary="Preview Dataset Rows",
    operation_id="query_preview_dataset",
    response_description="Sample preview rows of specified dataset.",
    responses=create_error_responses(400, 401, 403, 404, 500),
    description="Executes a sample preview query for a dataset.",
    dependencies=[Depends(require_permission("datasets:read"))],
)
def preview_dataset(
    dataset_id: str,
    limit: Annotated[int, Query(ge=1, le=500)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    _current_user: Annotated[
        User, Depends(get_current_user)
    ] = None,  # type: ignore[assignment]
    query_service: Annotated[
        QueryService, Depends(get_query_service)
    ] = None,  # type: ignore[assignment]
) -> QueryResultDTO:
    """Preview dataset sample rows with sensitive columns filtered."""
    result_vo = query_service.preview_dataset(
        dataset_id=dataset_id,
        limit=limit,
        offset=offset,
    )
    # Filter sensitive columns from preview results
    filtered_columns = [
        c for c in result_vo.columns
        if (c.name if hasattr(c, "name") else str(c)).lower()
        not in _SENSITIVE_COLUMNS
    ]
    if len(filtered_columns) < len(result_vo.columns):
        filtered_names = {
            c.name if hasattr(c, "name") else str(c)
            for c in filtered_columns
        }
        filtered_rows = [
            {k: v for k, v in row.items() if k in filtered_names}
            for row in result_vo.rows
        ]
        result_vo = replace(
            result_vo,
            columns=filtered_columns,
            rows=filtered_rows,
        )
    return _map_result_to_dto(result_vo)
