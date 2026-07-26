"""Pie Chart Builder implementation."""

from __future__ import annotations

from collections import defaultdict
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


class PieChartBuilder(BaseChartBuilder):
    """Builder for PIE_CHART visualizations."""

    @property
    def chart_type(self) -> ChartType:
        """Supported chart type."""
        return ChartType.PIE_CHART

    def build(self, result: QueryResult, config: ChartConfiguration) -> ChartResult:
        """Build a Pie Chart model from QueryResult and ChartConfiguration."""
        x_col = config.x_axis_column or result.columns[0].name
        y_col = (
            config.y_axis_columns[0]
            if config.y_axis_columns
            else result.columns[1].name
        )

        category_data: dict[str, list[Any]] = defaultdict(list)
        labels_order: list[str] = []
        seen_labels: set[str] = set()

        for row in result.rows:
            raw_x = row.get(x_col)
            lbl = self._format_label(raw_x)
            if lbl not in seen_labels:
                seen_labels.add(lbl)
                labels_order.append(lbl)
            category_data[lbl].append(row.get(y_col))

        colors = self.resolve_colors(config, len(labels_order))
        points: list[ChartPoint] = []

        for idx, lbl in enumerate(labels_order):
            val_list = category_data[lbl]
            agg_val = self.aggregate_values(val_list, config.aggregation)
            points.append(
                ChartPoint(
                    x=lbl,
                    y=agg_val,
                    label=lbl,
                    value=agg_val,
                    metadata={"color": colors[idx]},
                )
            )

        series = ChartSeries(
            name=y_col,
            data=points,
            chart_type=ChartType.PIE_CHART,
        )

        stats = self.compute_statistics([series])
        title = config.title or f"Pie Chart ({y_col} by {x_col})"
        subtitle = config.subtitle

        metadata = {
            "chart_type": ChartType.PIE_CHART.value,
            "x_axis": x_col,
            "y_axis": y_col,
            "aggregation": config.aggregation.value,
            "slice_count": len(points),
            "row_count": len(result.rows),
        }
        metadata.update(config.metadata)

        return ChartResult(
            title=title,
            subtitle=subtitle,
            labels=labels_order,
            series=[series],
            metadata=metadata,
            statistics=stats,
            recommended_colors=colors,
        )
