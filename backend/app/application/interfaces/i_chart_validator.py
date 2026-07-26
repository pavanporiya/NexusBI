"""Application interface for Chart Validation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.chart import ChartConfiguration
from app.domain.value_objects.query import QueryResult


class IChartValidator(ABC):
    """Abstract interface for chart configuration and dataset validator."""

    @abstractmethod
    def validate(self, result: QueryResult, config: ChartConfiguration) -> None:
        """Validate query result and chart configuration against chart invariants.

        Raises:
            ChartValidationError: If configuration or dataset fails validation.
        """
        ...
