"""Bar Chart Builder implementation."""

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


class BarChartBuilder(BaseChartBuilder):
    """Builder for BAR_CHART visualizations."""

    @property
    def chart_type(self) -> ChartType:
        """Supported chart type."""
        return ChartType.BAR_CHART

    def build(self, result: QueryResult, config: ChartConfiguration) -> ChartResult:
        """Build a Bar Chart model from QueryResult and ChartConfiguration."""
        x_col = config.x_axis_column or result.columns[0].name
        y_cols = config.y_axis_columns or [result.columns[1].name]
        group_col = config.group_by_column

        labels_order: list[str] = []
        seen_labels: set[str] = set()

        for row in result.rows:
            raw_x = row.get(x_col)
            formatted_x = self._format_label(raw_x)
            if formatted_x not in seen_labels:
                seen_labels.add(formatted_x)
                labels_order.append(formatted_x)

        series_list: list[ChartSeries] = []

        if group_col:
            # Grouping by secondary dimension
            # group_val -> label -> metric_val
            group_data: dict[str, dict[str, list[Any]]] = defaultdict(
                lambda: defaultdict(list)
            )

            y_metric_col = y_cols[0]
            for row in result.rows:
                raw_x = row.get(x_col)
                lbl = self._format_label(raw_x)
                grp_val = self._format_label(row.get(group_col))
                y_val = row.get(y_metric_col)
                group_data[grp_val][lbl].append(y_val)

            groups = list(group_data.keys())
            colors = self.resolve_colors(config, len(groups))

            for idx, grp_name in enumerate(groups):
                points: list[ChartPoint] = []
                for lbl in labels_order:
                    val_list = group_data[grp_name].get(lbl, [])
                    agg_val = self.aggregate_values(val_list, config.aggregation)
                    points.append(
                        ChartPoint(
                            x=lbl,
                            y=agg_val,
                            label=f"{grp_name} - {lbl}",
                            value=agg_val,
                        )
                    )
                series_list.append(
                    ChartSeries(
                        name=grp_name,
                        data=points,
                        color=colors[idx],
                        chart_type=ChartType.BAR_CHART,
                    )
                )

        else:
            # Standard multi-metric or single metric series
            # metric_col -> label -> list[val]
            metric_data: dict[str, dict[str, list[Any]]] = defaultdict(
                lambda: defaultdict(list)
            )

            for row in result.rows:
                raw_x = row.get(x_col)
                lbl = self._format_label(raw_x)
                for y_col in y_cols:
                    metric_data[y_col][lbl].append(row.get(y_col))

            colors = self.resolve_colors(config, len(y_cols))

            for idx, y_col in enumerate(y_cols):
                points = []
                for lbl in labels_order:
                    val_list = metric_data[y_col].get(lbl, [])
                    agg_val = self.aggregate_values(val_list, config.aggregation)
                    points.append(
                        ChartPoint(
                            x=lbl,
                            y=agg_val,
                            label=lbl,
                            value=agg_val,
                        )
                    )
                series_list.append(
                    ChartSeries(
                        name=y_col,
                        data=points,
                        color=colors[idx],
                        chart_type=ChartType.BAR_CHART,
                    )
                )

        colors_used = [s.color for s in series_list if s.color is not None]
        stats = self.compute_statistics(series_list)

        title = config.title or f"Bar Chart ({', '.join(y_cols)})"
        subtitle = config.subtitle

        metadata = {
            "chart_type": ChartType.BAR_CHART.value,
            "x_axis": x_col,
            "y_axes": y_cols,
            "group_by": group_col,
            "aggregation": config.aggregation.value,
            "row_count": len(result.rows),
        }
        metadata.update(config.metadata)

        return ChartResult(
            title=title,
            subtitle=subtitle,
            labels=labels_order,
            series=series_list,
            metadata=metadata,
            statistics=stats,
            recommended_colors=colors_used,
        )
