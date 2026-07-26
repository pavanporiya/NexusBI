"""Application interface for Chart Builders."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import ChartType
from app.domain.value_objects.chart import ChartConfiguration, ChartResult
from app.domain.value_objects.query import QueryResult


class IChartBuilder(ABC):
    """Abstract interface for chart type builder strategies."""

    @property
    @abstractmethod
    def chart_type(self) -> ChartType:
        """The supported chart type for this builder strategy."""
        ...

    @abstractmethod
    def build(self, result: QueryResult, config: ChartConfiguration) -> ChartResult:
        """Transform input data and config into a typed ChartResult model.

        Args:
            result: The validated QueryResult produced by the Query Engine.
            config: The ChartConfiguration specification.

        Returns:
            A structured, typed ChartResult model.
        """
        ...
