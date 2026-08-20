"""Chart Engine Data Transfer Objects (DTOs) for request/response serialization."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.application.dto.query_dto import QueryResultDTO


class ChartPointDTO(BaseModel):
    """Data Transfer Object representing a chart point."""

    x: Any = Field(..., description="X-axis category or value")
    y: Any = Field(..., description="Y-axis metric value")
    label: str | None = Field(default=None, description="Optional label for point")
    value: Any = Field(default=None, description="Optional value override")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Point metadata")


class ChartSeriesDTO(BaseModel):
    """Data Transfer Object representing a chart series."""

    name: str = Field(..., description="Series label or metric name")
    data: list[ChartPointDTO] = Field(
        default_factory=list, description="Series data points"
    )
    color: str | None = Field(default=None, description="Hex color override")
    chart_type: str | None = Field(
        default=None, description="Series specific chart type override"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Series metadata"
    )


class AxisDTO(BaseModel):
    """Data Transfer Object representing axis configuration."""

    name: str = Field(..., description="Axis column identifier")
    title: str | None = Field(default=None, description="Display title for axis")
    type: str = Field(default="x", description="Axis classification: x, y, series")
    data_type: str = Field(default="string", description="Axis data type")
    unit: str | None = Field(default=None, description="Unit suffix")
    min_val: float | None = Field(default=None, description="Min numeric bound")
    max_val: float | None = Field(default=None, description="Max numeric bound")


class LegendDTO(BaseModel):
    """Data Transfer Object representing legend layout."""

    show: bool = Field(default=True, description="Whether to display legend")
    position: str = Field(default="top", description="Legend position")
    labels: list[str] = Field(default_factory=list, description="Legend label strings")


class ColorPaletteDTO(BaseModel):
    """Data Transfer Object representing color palette settings."""

    name: str = Field(default="default", description="Palette theme name")
    colors: list[str] = Field(
        default_factory=list, description="Hex color strings array"
    )


class ChartConfigurationDTO(BaseModel):
    """Data Transfer Object representing chart generation parameters."""

    chart_type: str = Field(
        ...,
        description=(
            "Target chart type: kpi, table, bar_chart, line_chart, "
            "pie_chart, area_chart, donut_chart"
        ),
    )
    x_axis_column: str | None = Field(
        default=None, description="X-axis category/dimension column"
    )
    y_axis_columns: list[str] = Field(
        default_factory=list, description="Y-axis metric columns"
    )
    group_by_column: str | None = Field(
        default=None, description="Optional secondary grouping dimension"
    )
    aggregation: str = Field(
        default="sum",
        description=(
            "Aggregation operation: sum, avg, min, max, count, count_distinct, none"
        ),
    )
    title: str | None = Field(default=None, description="Chart header title")
    subtitle: str | None = Field(default=None, description="Chart header subtitle")
    color_palette: ColorPaletteDTO | str | None = Field(
        default=None, description="Color palette configuration"
    )
    legend: LegendDTO | None = Field(
        default=None, description="Legend placement settings"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration metadata"
    )


class ChartResultDTO(BaseModel):
    """Data Transfer Object representing built chart output model."""

    title: str = Field(..., description="Chart display title")
    subtitle: str | None = Field(default=None, description="Chart subtitle")
    labels: list[str] = Field(default_factory=list, description="Category axis labels")
    series: list[ChartSeriesDTO] = Field(
        default_factory=list, description="Data series array"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Execution and chart metadata"
    )
    statistics: dict[str, Any] = Field(
        default_factory=dict,
        description="Automated metric summary stats (min, max, average, count, sum)",
    )
    recommended_colors: list[str] = Field(
        default_factory=list, description="Palette hex colors assigned to series"
    )


class GenerateChartRequestDTO(BaseModel):
    """Data Transfer Object for generating a chart model from QueryResult."""

    result: QueryResultDTO = Field(..., description="Validated tabular query results")
    config: ChartConfigurationDTO = Field(
        ..., description="Chart configuration parameters"
    )


class PreviewChartRequestDTO(BaseModel):
    """Data Transfer Object for previewing a chart configuration."""

    result: QueryResultDTO = Field(..., description="Sample tabular query results")
    config: ChartConfigurationDTO = Field(
        ..., description="Chart configuration parameters"
    )


class ValidateChartRequestDTO(BaseModel):
    """Data Transfer Object for validating a chart config against result schema."""

    result: QueryResultDTO = Field(
        ..., description="Tabular query result schema and sample"
    )
    config: ChartConfigurationDTO = Field(
        ..., description="Chart configuration parameters"
    )


class ValidateChartResponseDTO(BaseModel):
    """Data Transfer Object for chart validation status response."""

    valid: bool = Field(..., description="Validation success flag")
    message: str = Field(..., description="Human readable message")
    errors: list[str] = Field(
        default_factory=list, description="List of validation errors if invalid"
    )


class ChartSpecDTO(BaseModel):
    """Data Transfer Object representing a structured chart specification."""

    type: str = Field(..., description="Chart type: line, bar, area, pie, table")
    title: str = Field(..., description="Chart display title")
    x_axis: str | None = Field(default=None, description="X-axis category/dimension")
    y_axis: Any = Field(default=None, description="Y-axis metric(s)")
    data: list[dict[str, Any]] = Field(default_factory=list, description="Data points")
    series: list[dict[str, Any]] | None = Field(
        default=None, description="Series details"
    )
    labels: list[str] | None = Field(default=None, description="Category labels")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Chart metadata")
