"""Application interface for Chart Formatting."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.value_objects.chart import ChartResult


class IChartFormatter(ABC):
    """Abstract interface for serializing and formatting ChartResult models."""

    @abstractmethod
    def format(self, chart_result: ChartResult) -> dict[str, Any]:
        """Format a ChartResult value object into a serializable dictionary.

        Args:
            chart_result: The constructed ChartResult domain VO.

        Returns:
            Structured dictionary matching API JSON specifications.
        """
        ...
