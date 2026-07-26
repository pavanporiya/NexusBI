"""Domain value objects for the Universal Chart Engine.

Framework-independent, strongly typed immutable value objects representing
charts, series, data points, axes, legends, color palettes, configurations, and results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import AggregationType, AxisType, ChartType
from app.domain.exceptions import ChartValidationError

DEFAULT_COLORS: list[str] = [
    "#3B82F6",  # Blue
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#EF4444",  # Red
    "#8B5CF6",  # Purple
    "#EC4899",  # Pink
    "#14B8A6",  # Teal
    "#F97316",  # Orange
]


@dataclass(frozen=True, slots=True)
class ChartPoint:
    """Value object representing an individual data point in a chart series."""

    x: Any
    y: Any
    label: str | None = None
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChartSeries:
    """Value object representing a series of data points in a chart."""

    name: str
    data: list[ChartPoint] = field(default_factory=list)
    color: str | None = None
    chart_type: ChartType | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate non-empty series name."""
        if not self.name or not self.name.strip():
            raise ChartValidationError("ChartSeries name must not be empty.")
        object.__setattr__(self, "name", self.name.strip())


@dataclass(frozen=True, slots=True)
class Axis:
    """Value object defining axis properties and metadata."""

    name: str
    title: str | None = None
    type: AxisType = AxisType.X
    data_type: str = "string"
    unit: str | None = None
    min_val: float | None = None
    max_val: float | None = None

    def __post_init__(self) -> None:
        """Validate axis parameters."""
        if not self.name or not self.name.strip():
            raise ChartValidationError("Axis name must not be empty.")
        object.__setattr__(self, "name", self.name.strip())


@dataclass(frozen=True, slots=True)
class Legend:
    """Value object defining legend configuration."""

    show: bool = True
    position: str = "top"
    labels: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ColorPalette:
    """Value object defining color palettes for visualization rendering."""

    name: str = "default"
    colors: list[str] = field(default_factory=lambda: list(DEFAULT_COLORS))

    def __post_init__(self) -> None:
        """Ensure non-empty color list."""
        if not self.colors:
            object.__setattr__(self, "colors", list(DEFAULT_COLORS))


@dataclass(frozen=True, slots=True)
class ChartConfiguration:
    """Value object encapsulating chart building parameters and visualization setup."""

    chart_type: ChartType
    x_axis_column: str | None = None
    y_axis_columns: list[str] = field(default_factory=list)
    group_by_column: str | None = None
    aggregation: AggregationType = AggregationType.SUM
    title: str | None = None
    subtitle: str | None = None
    color_palette: ColorPalette | str = field(default_factory=ColorPalette)
    legend: Legend = field(default_factory=Legend)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize configuration parameters."""
        chart_t = (
            ChartType.from_str(self.chart_type)
            if isinstance(self.chart_type, str)
            else self.chart_type
        )
        object.__setattr__(self, "chart_type", chart_t)

        agg = (
            AggregationType.from_str(self.aggregation)
            if isinstance(self.aggregation, str)
            else self.aggregation
        )
        object.__setattr__(self, "aggregation", agg)

        if isinstance(self.color_palette, str):
            palette = ColorPalette(name=self.color_palette)
            object.__setattr__(self, "color_palette", palette)


@dataclass(frozen=True, slots=True)
class Chart:
    """Domain model representing a chart instance configuration definition."""

    title: str
    chart_type: ChartType
    config: ChartConfiguration
    id: str | None = None
    subtitle: str | None = None

    def __post_init__(self) -> None:
        """Validate chart title and chart type."""
        if not self.title or not self.title.strip():
            raise ChartValidationError("Chart title must not be empty.")
        object.__setattr__(self, "title", self.title.strip())


@dataclass(frozen=True, slots=True)
class ChartResult:
    """Value object capturing the structured result of a built chart model."""

    title: str
    subtitle: str | None
    labels: list[str]
    series: list[ChartSeries]
    metadata: dict[str, Any]
    statistics: dict[str, Any]
    recommended_colors: list[str]
