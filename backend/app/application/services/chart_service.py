"""Application service for the Universal Chart Engine."""

from __future__ import annotations

from typing import Any

from app.application.interfaces.i_chart_formatter import IChartFormatter
from app.application.interfaces.i_chart_validator import IChartValidator
from app.domain.exceptions import ChartValidationError
from app.domain.value_objects.chart import ChartConfiguration, ChartResult
from app.domain.value_objects.query import QueryResult
from app.infrastructure.chart.formatter import DefaultChartFormatter
from app.infrastructure.chart.registry import ChartBuilderRegistry
from app.infrastructure.chart.validator import DefaultChartValidator


class ChartService:
    """Orchestrates validation, builder execution, and result formatting."""

    def __init__(
        self,
        validator: IChartValidator | None = None,
        formatter: IChartFormatter | None = None,
    ) -> None:
        self.validator = validator or DefaultChartValidator()
        self.formatter = formatter or DefaultChartFormatter()

    def generate_chart(
        self, result: QueryResult, config: ChartConfiguration
    ) -> ChartResult:
        """Validate QueryResult and ChartConfiguration and return built ChartResult.

        Args:
            result: The validated QueryResult from Query Engine.
            config: Chart build configuration parameters.

        Returns:
            Structured ChartResult domain model.
        """
        self.validator.validate(result, config)
        builder = ChartBuilderRegistry.get(config.chart_type)
        return builder.build(result, config)

    def preview_chart(
        self, result: QueryResult, config: ChartConfiguration
    ) -> ChartResult:
        """Generate a preview ChartResult from a sample dataset.

        Args:
            result: Sample QueryResult dataset.
            config: Chart configuration parameters.

        Returns:
            Structured preview ChartResult domain model.
        """
        return self.generate_chart(result, config)

    def validate_chart(
        self, result: QueryResult, config: ChartConfiguration
    ) -> dict[str, Any]:
        """Validate chart parameters without generating the full chart model.

        Args:
            result: QueryResult dataset.
            config: Chart configuration parameters.

        Returns:
            Dictionary payload with validation success flag, message, and error details.
        """
        try:
            self.validator.validate(result, config)
            return {
                "valid": True,
                "message": (
                    "Chart configuration is valid and compatible with the "
                    "dataset schema."
                ),
                "errors": [],
            }
        except ChartValidationError as exc:
            return {
                "valid": False,
                "message": str(exc),
                "errors": [str(exc)],
            }

    def format_chart(self, chart_result: ChartResult) -> dict[str, Any]:
        """Format ChartResult domain model into a serializable API dictionary."""
        return self.formatter.format(chart_result)
