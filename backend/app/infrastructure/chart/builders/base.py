"""Base chart builder strategy implementation providing common utilities."""

from __future__ import annotations

from abc import ABC
from decimal import Decimal
from typing import Any

from app.application.interfaces.i_chart_builder import IChartBuilder
from app.domain.enums import AggregationType
from app.domain.value_objects.chart import (
    DEFAULT_COLORS,
    ChartConfiguration,
    ChartSeries,
)


class BaseChartBuilder(IChartBuilder, ABC):
    """Abstract base builder with shared data and aggregation helpers."""

    def compute_statistics(self, series_list: list[ChartSeries]) -> dict[str, Any]:
        """Automatically compute summary metrics: min, max, average, count, sum."""
        numeric_values: list[float] = []

        for series in series_list:
            for point in series.data:
                val = point.y if point.y is not None else point.value
                numeric_val = self._to_float(val)
                if numeric_val is not None:
                    numeric_values.append(numeric_val)

        if not numeric_values:
            return {
                "min": 0,
                "max": 0,
                "average": 0,
                "count": 0,
                "sum": 0,
            }

        total_sum = float(sum(numeric_values))
        count = len(numeric_values)
        avg = float(round(total_sum / count, 4)) if count > 0 else 0.0
        min_val = float(min(numeric_values))
        max_val = float(max(numeric_values))

        # Return int if whole numbers, else float rounded to 4 decimals
        return {
            "min": int(min_val) if min_val.is_integer() else round(min_val, 4),
            "max": int(max_val) if max_val.is_integer() else round(max_val, 4),
            "average": int(avg) if avg.is_integer() else avg,
            "count": count,
            "sum": int(total_sum) if total_sum.is_integer() else round(total_sum, 4),
        }

    def aggregate_values(self, values: list[Any], aggregation: AggregationType) -> Any:
        """Apply aggregation function across a sequence of values."""
        clean_values = [v for v in values if v is not None]
        if not clean_values:
            return 0 if aggregation != AggregationType.NONE else None

        if aggregation == AggregationType.COUNT:
            return len(clean_values)

        if aggregation == AggregationType.COUNT_DISTINCT:
            return len(set(clean_values))

        nums = [f for f in (self._to_float(v) for v in clean_values) if f is not None]
        if not nums:
            return clean_values[-1] if aggregation == AggregationType.NONE else 0

        if aggregation == AggregationType.SUM:
            s = sum(nums)
            return int(s) if s.is_integer() else round(s, 4)

        if aggregation in (AggregationType.AVG, AggregationType.AVERAGE):
            a = sum(nums) / len(nums)
            return int(a) if a.is_integer() else round(a, 4)

        if aggregation == AggregationType.MIN:
            m = min(nums)
            return int(m) if m.is_integer() else round(m, 4)

        if aggregation == AggregationType.MAX:
            mx = max(nums)
            return int(mx) if mx.is_integer() else round(mx, 4)

        # AggregationType.NONE or default fallback
        last = nums[-1]
        return int(last) if last.is_integer() else round(last, 4)

    def resolve_colors(self, config: ChartConfiguration, count: int) -> list[str]:
        """Resolve recommended color list for series/slices."""
        colors = DEFAULT_COLORS
        if config.color_palette and hasattr(config.color_palette, "colors"):
            if config.color_palette.colors:
                colors = config.color_palette.colors

        result_colors = []
        for i in range(count):
            result_colors.append(colors[i % len(colors)])
        return result_colors

    @staticmethod
    def _to_float(val: Any) -> float | None:
        """Helper to safely parse numeric values to float."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, Decimal):
            return float(val)
        if isinstance(val, bool):
            return 1.0 if val else 0.0
        if isinstance(val, str):
            try:
                return float(val.strip().replace(",", ""))
            except ValueError:
                return None
        return None

    @staticmethod
    def _format_label(val: Any) -> str:
        """Format an X-axis category or label string."""
        if val is None:
            return "Null"
        return str(val)
