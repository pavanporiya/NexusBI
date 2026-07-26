"""Universal Chart Engine REST API endpoints (v1 namespace)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_chart_service,
    get_current_user,
    require_permission,
)
from app.application.dto.chart_dto import (
    ChartConfigurationDTO,
    ChartPointDTO,
    ChartResultDTO,
    ChartSeriesDTO,
    ColorPaletteDTO,
    GenerateChartRequestDTO,
    PreviewChartRequestDTO,
    ValidateChartRequestDTO,
    ValidateChartResponseDTO,
)
from app.application.dto.error_dto import create_error_responses
from app.application.dto.query_dto import QueryResultDTO
from app.application.services.chart_service import ChartService
from app.core.exceptions import ValidationError
from app.domain.entities.user import User
from app.domain.enums import AggregationType, ChartType
from app.domain.exceptions import ChartValidationError
from app.domain.value_objects.chart import (
    ChartConfiguration,
    ChartResult,
    ColorPalette,
    Legend,
)
from app.domain.value_objects.query import QueryColumn, QueryMetadata, QueryResult

router = APIRouter(prefix="/charts", tags=["Universal Chart Engine"])


def _resolve_chart_inputs(
    dto_result: QueryResultDTO,
    dto_config: ChartConfigurationDTO,
) -> tuple[QueryResult, ChartConfiguration]:
    """Convert API DTOs into validated chart domain inputs."""
    try:
        return (
            _map_dto_to_query_result(dto_result),
            _map_dto_to_chart_config(dto_config),
        )
    except (ChartValidationError, ValueError) as exc:
        raise ValidationError(
            message="Chart configuration is invalid",
            detail=str(exc),
        ) from exc


def _map_dto_to_query_result(dto_result: QueryResultDTO) -> QueryResult:
    """Map QueryResultDTO payload to domain QueryResult value object."""
    cols = [QueryColumn(name=c.name, type=c.type) for c in dto_result.columns]
    col_types = dto_result.column_types or {c.name: c.type for c in cols}
    metadata = QueryMetadata(
        execution_time=dto_result.metadata.execution_time,
        row_count=dto_result.metadata.row_count,
        columns=cols,
        truncated=dto_result.metadata.truncated,
        limit=dto_result.metadata.limit,
        offset=dto_result.metadata.offset,
    )
    return QueryResult(
        rows=dto_result.rows,
        columns=cols,
        column_types=col_types,
        execution_time=dto_result.execution_time,
        row_count=dto_result.row_count,
        metadata=metadata,
    )


def _map_dto_to_chart_config(dto_config: ChartConfigurationDTO) -> ChartConfiguration:
    """Map ChartConfigurationDTO payload to domain ChartConfiguration value object."""
    palette: ColorPalette | str = "default"
    if dto_config.color_palette:
        if isinstance(dto_config.color_palette, str):
            palette = ColorPalette(name=dto_config.color_palette)
        elif isinstance(dto_config.color_palette, ColorPaletteDTO):
            palette = ColorPalette(
                name=dto_config.color_palette.name,
                colors=dto_config.color_palette.colors,
            )

    legend = Legend()
    if dto_config.legend:
        legend = Legend(
            show=dto_config.legend.show,
            position=dto_config.legend.position,
            labels=dto_config.legend.labels,
        )

    return ChartConfiguration(
        chart_type=ChartType.from_str(dto_config.chart_type),
        x_axis_column=dto_config.x_axis_column,
        y_axis_columns=dto_config.y_axis_columns,
        group_by_column=dto_config.group_by_column,
        aggregation=AggregationType.from_str(dto_config.aggregation),
        title=dto_config.title,
        subtitle=dto_config.subtitle,
        color_palette=palette,
        legend=legend,
        metadata=dto_config.metadata,
    )


def _map_chart_result_to_dto(chart_res: ChartResult) -> ChartResultDTO:
    """Map domain ChartResult value object to ChartResultDTO payload."""
    return ChartResultDTO(
        title=chart_res.title,
        subtitle=chart_res.subtitle,
        labels=chart_res.labels,
        series=[
            ChartSeriesDTO(
                name=s.name,
                data=[
                    ChartPointDTO(
                        x=pt.x,
                        y=pt.y,
                        label=pt.label,
                        value=pt.value,
                        metadata=pt.metadata,
                    )
                    for pt in s.data
                ],
                color=s.color,
                chart_type=s.chart_type.value if s.chart_type else None,
                metadata=s.metadata,
            )
            for s in chart_res.series
        ],
        metadata=chart_res.metadata,
        statistics=chart_res.statistics,
        recommended_colors=chart_res.recommended_colors,
    )


@router.post(
    "/generate",
    response_model=ChartResultDTO,
    status_code=status.HTTP_200_OK,
    summary="Generate Chart Model",
    operation_id="charts_generate",
    response_description="Structured visualization chart model.",
    responses=create_error_responses(400, 401, 403, 422, 500),
    description=(
        "Transforms a QueryResult and ChartConfiguration into a typed "
        "visualization model."
    ),
    dependencies=[Depends(require_permission("datasets:read"))],
)
def generate_chart(
    dto: GenerateChartRequestDTO,
    _current_user: Annotated[User, Depends(get_current_user)],
    chart_service: Annotated[ChartService, Depends(get_chart_service)],
) -> ChartResultDTO:
    """Transform QueryResult into a structured ChartResult model."""
    query_result, chart_config = _resolve_chart_inputs(dto.result, dto.config)
    try:
        result_vo = chart_service.generate_chart(query_result, chart_config)
    except ChartValidationError as exc:
        raise ValidationError(
            message="Chart generation failed",
            detail=str(exc),
        ) from exc
    return _map_chart_result_to_dto(result_vo)


@router.post(
    "/preview",
    response_model=ChartResultDTO,
    status_code=status.HTTP_200_OK,
    summary="Preview Chart Configuration",
    operation_id="charts_preview",
    response_description="Sample preview chart visualization model.",
    responses=create_error_responses(400, 401, 403, 422, 500),
    description="Generates a preview visualization model from sample query results.",
    dependencies=[Depends(require_permission("datasets:read"))],
)
def preview_chart(
    dto: PreviewChartRequestDTO,
    _current_user: Annotated[User, Depends(get_current_user)],
    chart_service: Annotated[ChartService, Depends(get_chart_service)],
) -> ChartResultDTO:
    """Preview a chart configuration with sample dataset rows."""
    query_result, chart_config = _resolve_chart_inputs(dto.result, dto.config)
    try:
        result_vo = chart_service.preview_chart(query_result, chart_config)
    except ChartValidationError as exc:
        raise ValidationError(
            message="Chart preview failed",
            detail=str(exc),
        ) from exc
    return _map_chart_result_to_dto(result_vo)


@router.post(
    "/validate",
    response_model=ValidateChartResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Validate Chart Configuration",
    operation_id="charts_validate",
    response_description="Chart validation status confirmation.",
    responses=create_error_responses(400, 401, 403, 422, 500),
    description=(
        "Validates a chart configuration against dataset columns without "
        "constructing full series."
    ),
    dependencies=[Depends(require_permission("datasets:read"))],
)
def validate_chart(
    dto: ValidateChartRequestDTO,
    _current_user: Annotated[User, Depends(get_current_user)],
    chart_service: Annotated[ChartService, Depends(get_chart_service)],
) -> ValidateChartResponseDTO:
    """Validate chart configuration against query result schema."""
    query_result, chart_config = _resolve_chart_inputs(dto.result, dto.config)
    val_res = chart_service.validate_chart(query_result, chart_config)
    return ValidateChartResponseDTO(
        valid=val_res["valid"],
        message=val_res["message"],
        errors=val_res.get("errors", []),
    )
