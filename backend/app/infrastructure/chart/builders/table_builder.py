"""Table Chart Builder implementation."""

from __future__ import annotations

from typing import Any

from app.domain.enums import ChartType
from app.domain.value_objects.chart import (
    ChartConfiguration,
    ChartPoint,
    ChartResult,
    ChartSeries,
)
from app.domain.value_objects.query import QueryResult
from app.infrastructure.chart.builders.base import BaseChartBuilder


class TableBuilder(BaseChartBuilder):
    """Builder for TABLE chart model visualizations."""

    @property
    def chart_type(self) -> ChartType:
        """Supported chart type."""
        return ChartType.TABLE

    def build(self, result: QueryResult, config: ChartConfiguration) -> ChartResult:
        """Build a Table Chart model from QueryResult and ChartConfiguration."""
        cols_to_include = [c.name for c in result.columns]
        colors = self.resolve_colors(config, len(cols_to_include))

        series_list: list[ChartSeries] = []

        for idx, col_name in enumerate(cols_to_include):
            points: list[ChartPoint] = []
            for row_idx, row in enumerate(result.rows):
                val: Any = row.get(col_name)
                num_val = self._to_float(val)
                points.append(
                    ChartPoint(
                        x=row_idx,
                        y=num_val if num_val is not None else val,
                        label=col_name,
                        value=val,
                    )
                )
            series_list.append(
                ChartSeries(
                    name=col_name,
                    data=points,
                    color=colors[idx],
                    chart_type=ChartType.TABLE,
                )
            )

        stats = self.compute_statistics(series_list)
        title = config.title or "Data Table"
        subtitle = config.subtitle

        metadata = {
            "chart_type": ChartType.TABLE.value,
            "columns": cols_to_include,
            "row_count": len(result.rows),
        }
        metadata.update(config.metadata)

        return ChartResult(
            title=title,
            subtitle=subtitle,
            labels=cols_to_include,
            series=series_list,
            metadata=metadata,
            statistics=stats,
            recommended_colors=[s.color for s in series_list if s.color],
        )
