"""Query Engine REST API endpoints (v1 namespace)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_current_user,
    get_query_service,
    require_permission,
)
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


def _map_metadata_to_dto(meta: QueryMetadata) -> QueryMetadataDTO:
    """Map domain QueryMetadata value object to QueryMetadataDTO."""
    return QueryMetadataDTO(
        statistics=QueryStatisticsDTO(
            query_plan=meta.statistics.query_plan,
            rows_scanned=meta.statistics.rows_scanned,
            bytes_processed=meta.statistics.bytes_processed,
            cache_hit=meta.statistics.cache_hit,
        ),
        execution_time=meta.execution_time,
        row_count=meta.row_count,
        columns=[QueryColumnDTO(name=c.name, type=c.type) for c in meta.columns],
        truncated=meta.truncated,
        limit=meta.limit,
        offset=meta.offset,
    )


def _map_result_to_dto(result: QueryResult) -> QueryResultDTO:
    """Map domain QueryResult value object to QueryResultDTO."""
    return QueryResultDTO(
        rows=result.rows,
        columns=[QueryColumnDTO(name=c.name, type=c.type) for c in result.columns],
        column_types=result.column_types,
        execution_time=result.execution_time,
        row_count=result.row_count,
        metadata=_map_metadata_to_dto(result.metadata),
    )


@router.post(
    "/validate",
    response_model=ValidateQueryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Validate SQL Query",
    operation_id="query_validate",
    response_description="Validation status confirmation.",
    responses=create_error_responses(400, 401, 403, 422, 500),
    description="Validates SQL query against AST security rules.",
    dependencies=[Depends(require_permission("datasets:read"))],
)
def validate_query(
    dto: ValidateQueryRequestDTO,
    _current_user: Annotated[User, Depends(get_current_user)],
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> ValidateQueryResponseDTO:
    """Validate a SQL query without executing it."""
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
    response_description="Tabular query results with execution metadata.",
    responses=create_error_responses(400, 401, 403, 500, 504),
    description="Safely executes a SELECT query with parameter binding.",
    dependencies=[Depends(require_permission("datasets:read"))],
)
def execute_query(
    dto: ExecuteQueryRequestDTO,
    _current_user: Annotated[User, Depends(get_current_user)],
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> QueryResultDTO:
    """Execute a read-only query and return formatted tabular results."""
    request_vo = QueryRequest.create(
        sql=dto.sql,
        parameters=dto.parameters,
        page=dto.page,
        page_size=dto.page_size,
        limit=dto.limit,
        offset=dto.offset,
        timeout=dto.timeout,
    )
    result_vo = query_service.execute(request_vo)
    return _map_result_to_dto(result_vo)


@router.post(
    "/explain",
    response_model=QueryMetadataDTO,
    status_code=status.HTTP_200_OK,
    summary="Explain SQL Query Plan",
    operation_id="query_explain",
    response_description="Query execution plan metadata.",
    responses=create_error_responses(400, 401, 403, 500),
    description="Generates query plan metadata without fetching dataset rows.",
    dependencies=[Depends(require_permission("datasets:read"))],
)
def explain_query(
    dto: ExplainQueryRequestDTO,
    _current_user: Annotated[User, Depends(get_current_user)],
    query_service: Annotated[QueryService, Depends(get_query_service)],
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
    _current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    query_service: Annotated[QueryService, Depends(get_query_service)] = None,  # type: ignore[assignment]
) -> QueryResultDTO:
    """Preview dataset sample rows."""
    result_vo = query_service.preview_dataset(
        dataset_id=dataset_id,
        limit=limit,
        offset=offset,
    )
    return _map_result_to_dto(result_vo)
