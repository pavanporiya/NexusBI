"""Default Chart Validator implementing IChartValidator.

Validates chart configurations and QueryResult datasets against domain validation rules:
- Empty datasets
- Unsupported chart types
- Missing x-axis
- Missing y-axis
- Duplicate series
- Null values
- Invalid aggregations
"""

from __future__ import annotations

from typing import Any

from app.application.interfaces.i_chart_validator import IChartValidator
from app.domain.enums import AggregationType, ChartType
from app.domain.exceptions import ChartValidationError
from app.domain.value_objects.chart import ChartConfiguration
from app.domain.value_objects.query import QueryResult


class DefaultChartValidator(IChartValidator):
    """Validator enforcing chart engine data and configuration invariants."""

    def validate(self, result: QueryResult, config: ChartConfiguration) -> None:
        """Validate QueryResult and ChartConfiguration against chart invariants.

        Raises:
            ChartValidationError: If validation rules are violated.
        """
        # 1. Unsupported Chart Type
        try:
            chart_t = ChartType.from_str(config.chart_type)
        except ValueError as exc:
            raise ChartValidationError(
                f"Unsupported chart type: {config.chart_type}"
            ) from exc

        # 2. Empty Dataset
        if not result.rows:
            raise ChartValidationError(
                "Dataset is empty. Cannot generate chart from empty query results."
            )

        column_names = {c.name for c in result.columns}

        # 3. Invalid Aggregation
        try:
            AggregationType.from_str(config.aggregation)
        except ValueError as exc:
            raise ChartValidationError(
                f"Invalid aggregation type: {config.aggregation}"
            ) from exc

        # 4. Duplicate Series Validation
        if config.y_axis_columns:
            seen_y = set()
            duplicates = []
            for y_col in config.y_axis_columns:
                if y_col in seen_y:
                    duplicates.append(y_col)
                seen_y.add(y_col)
            if duplicates:
                raise ChartValidationError(
                    f"Duplicate series columns detected: {', '.join(duplicates)}"
                )

        # Chart-type specific axis requirements
        if chart_t in (
            ChartType.BAR_CHART,
            ChartType.LINE_CHART,
            ChartType.AREA_CHART,
            ChartType.PIE_CHART,
            ChartType.DONUT_CHART,
        ):
            # Missing X-Axis
            if not config.x_axis_column or not config.x_axis_column.strip():
                raise ChartValidationError(
                    f"X-axis column is required for chart type '{chart_t.value}'."
                )
            if config.x_axis_column not in column_names:
                raise ChartValidationError(
                    f"X-axis column '{config.x_axis_column}' not found in "
                    "query result columns."
                )

            # Missing Y-Axis
            if not config.y_axis_columns:
                raise ChartValidationError(
                    "Y-axis metric column(s) are required for chart type "
                    f"'{chart_t.value}'."
                )

        if chart_t == ChartType.KPI:
            # KPI requires at least 1 metric y_axis_column or fallback column
            if not config.y_axis_columns and not config.x_axis_column:
                raise ChartValidationError(
                    "KPI card requires at least one target metric column "
                    "specified in y_axis_columns."
                )

        # Check existence of specified Y-axis columns
        for y_col in config.y_axis_columns:
            if y_col not in column_names:
                raise ChartValidationError(
                    f"Y-axis column '{y_col}' not found in query result columns."
                )

        # Check group_by column if present
        if config.group_by_column and config.group_by_column not in column_names:
            raise ChartValidationError(
                f"Group by column '{config.group_by_column}' not found in "
                "query result columns."
            )

        # 5. Null values check in metric columns
        self._validate_null_values(result, config)

    def _validate_null_values(
        self, result: QueryResult, config: ChartConfiguration
    ) -> None:
        """Inspect rows for null values and ensure metric columns have valid data."""
        for y_col in config.y_axis_columns:
            all_null = True
            for row in result.rows:
                val: Any = row.get(y_col)
                if val is not None:
                    all_null = False
                    break
            if all_null and len(result.rows) > 0:
                raise ChartValidationError(
                    f"Metric column '{y_col}' contains only null values "
                    "across all rows."
                )
