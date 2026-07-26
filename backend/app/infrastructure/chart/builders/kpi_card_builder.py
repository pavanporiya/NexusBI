"""KPI Card Builder implementation."""

from __future__ import annotations

from app.domain.enums import ChartType
from app.domain.value_objects.chart import (
    ChartConfiguration,
    ChartPoint,
    ChartResult,
    ChartSeries,
)
from app.domain.value_objects.query import QueryResult
from app.infrastructure.chart.builders.base import BaseChartBuilder


class KPICardBuilder(BaseChartBuilder):
    """Builder for KPI card scalar visualizations."""

    @property
    def chart_type(self) -> ChartType:
        """Supported chart type."""
        return ChartType.KPI

    def build(self, result: QueryResult, config: ChartConfiguration) -> ChartResult:
        """Build a KPI Card model from QueryResult and ChartConfiguration."""
        metric_col = (
            config.y_axis_columns[0]
            if config.y_axis_columns
            else (config.x_axis_column or result.columns[0].name)
        )

        all_values = [row.get(metric_col) for row in result.rows]
        kpi_value = self.aggregate_values(all_values, config.aggregation)

        colors = self.resolve_colors(config, 1)

        point = ChartPoint(
            x=metric_col,
            y=kpi_value,
            label=config.title or metric_col,
            value=kpi_value,
        )

        series = ChartSeries(
            name=metric_col,
            data=[point],
            color=colors[0],
            chart_type=ChartType.KPI,
        )

        stats = self.compute_statistics([series])
        title = config.title or f"KPI ({metric_col})"
        subtitle = config.subtitle

        metadata = {
            "chart_type": ChartType.KPI.value,
            "metric_column": metric_col,
            "aggregation": config.aggregation.value,
            "kpi_value": kpi_value,
            "row_count": len(result.rows),
        }
        metadata.update(config.metadata)

        return ChartResult(
            title=title,
            subtitle=subtitle,
            labels=[metric_col],
            series=[series],
            metadata=metadata,
            statistics=stats,
            recommended_colors=[colors[0]],
        )
