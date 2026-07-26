"""Default Chart Formatter implementing IChartFormatter."""

from __future__ import annotations

from typing import Any

from app.application.interfaces.i_chart_formatter import IChartFormatter
from app.domain.value_objects.chart import ChartResult


class DefaultChartFormatter(IChartFormatter):
    """Formats ChartResult value objects into API response dictionaries."""

    def format(self, chart_result: ChartResult) -> dict[str, Any]:
        """Serialize a ChartResult model to a structured dictionary representation."""
        return {
            "title": chart_result.title,
            "subtitle": chart_result.subtitle,
            "labels": list(chart_result.labels),
            "series": [
                {
                    "name": s.name,
                    "data": [
                        {
                            "x": pt.x,
                            "y": pt.y,
                            "label": pt.label,
                            "value": pt.value,
                            "metadata": pt.metadata,
                        }
                        for pt in s.data
                    ],
                    "color": s.color,
                    "chart_type": s.chart_type.value if s.chart_type else None,
                    "metadata": s.metadata,
                }
                for s in chart_result.series
            ],
            "metadata": chart_result.metadata,
            "statistics": chart_result.statistics,
            "recommended_colors": list(chart_result.recommended_colors),
        }
