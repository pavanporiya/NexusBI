"""Application service for AI Agent Data Analyst visualization capabilities.

Bridges authorized query execution results and the Universal Chart Engine:
1. Determines if a business question/result benefits from visualization.
2. Selects an appropriate chart strategy (line, bar, area, pie, table).
3. Constructs and validates structured chart specifications using Pydantic.
4. Leverages existing ChartService to generate normalized chart models.
"""

from __future__ import annotations

from typing import Any

from app.application.services.chart_service import ChartService
from app.core.exceptions import ValidationError
from app.domain.enums import AggregationType, ChartType
from app.domain.exceptions import ChartValidationError
from app.domain.value_objects.chart import ChartConfiguration
from app.domain.value_objects.chart_spec import SUPPORTED_V1_CHART_TYPES, ChartSpec
from app.domain.value_objects.query import QueryResult


class VisualizationService:
    """Service for decision-making and generation of structured chart specs.

    Parameters
    ----------
    chart_service : ChartService | None
        Existing Universal Chart Engine service.
    """

    def __init__(self, chart_service: ChartService | None = None) -> None:
        self._chart_service = chart_service or ChartService()

    def should_visualize(
        self, natural_language_query: str, query_result: QueryResult
    ) -> bool:
        """Determine whether the query result benefits from visualization.

        Returns True if result is non-empty and contains suitable columns.
        """
        if not query_result or not query_result.rows or query_result.row_count == 0:
            return False

        visual_keywords = [
            "chart",
            "plot",
            "graph",
            "show",
            "trend",
            "monthly",
            "yearly",
            "daily",
            "sales",
            "revenue",
            "distribution",
            "breakdown",
            "comparison",
            "by",
            "over time",
            "percentage",
            "share",
            "top",
        ]
        query_lower = natural_language_query.lower()
        has_keyword = any(kw in query_lower for kw in visual_keywords)

        cols = [c.name for c in query_result.columns]
        if len(cols) >= 2 or has_keyword:
            return True

        return False

    def select_chart_type(
        self, natural_language_query: str, query_result: QueryResult
    ) -> tuple[str, str | None, list[str]]:
        """Determine optimal chart type and (x_axis, y_axis_columns) mapping.

        Returns
        -------
        tuple[str, str | None, list[str]]
            (chart_type, x_axis_column, y_axis_columns)
        """
        query_lower = natural_language_query.lower()
        cols = [c.name for c in query_result.columns]
        col_types = query_result.column_types or {}

        if not cols:
            return "table", None, []

        temporal_names = {
            "month",
            "year",
            "date",
            "day",
            "created_at",
            "timestamp",
            "period",
            "time",
            "dt",
            "quarter",
        }
        x_axis: str | None = None
        for col in cols:
            col_lower = col.lower()
            if col_lower in temporal_names or any(
                t in col_lower for t in ("date", "month", "year", "time")
            ):
                x_axis = col
                break

        numeric_types = {
            "integer",
            "bigint",
            "float",
            "numeric",
            "decimal",
            "double",
            "number",
            "int",
        }
        y_axis_cols: list[str] = []
        for col in cols:
            if col == x_axis:
                continue
            ctype = str(col_types.get(col, "")).lower()
            if ctype in numeric_types or any(
                nt in ctype for nt in ("int", "num", "float", "dec", "double")
            ):
                y_axis_cols.append(col)
            elif not ctype and any(
                m in col.lower()
                for m in (
                    "sales",
                    "revenue",
                    "count",
                    "amount",
                    "total",
                    "avg",
                    "sum",
                    "price",
                    "profit",
                    "qty",
                    "quantity",
                )
            ):
                y_axis_cols.append(col)

        if not x_axis:
            for col in cols:
                if col not in y_axis_cols:
                    x_axis = col
                    break
            if not x_axis and cols:
                x_axis = cols[0]
                if x_axis in y_axis_cols:
                    y_axis_cols.remove(x_axis)

        if not y_axis_cols and len(cols) > 1:
            y_axis_cols = [c for c in cols if c != x_axis][:1]

        if "line" in query_lower:
            return "line", x_axis, y_axis_cols
        if "area" in query_lower:
            return "area", x_axis, y_axis_cols
        if "pie" in query_lower:
            if len(query_result.rows) <= 10 and x_axis and y_axis_cols:
                return "pie", x_axis, y_axis_cols
            return "bar", x_axis, y_axis_cols
        if "bar" in query_lower or "histogram" in query_lower:
            return "bar", x_axis, y_axis_cols
        if "table" in query_lower:
            return "table", x_axis, y_axis_cols

        if x_axis and (
            x_axis.lower() in temporal_names
            or any(t in x_axis.lower() for t in ("date", "month", "year"))
        ):
            if "area" in query_lower or "cumulative" in query_lower:
                return "area", x_axis, y_axis_cols
            return "line", x_axis, y_axis_cols

        if (
            any(
                kw in query_lower
                for kw in ("share", "proportion", "breakdown", "percentage")
            )
            and len(query_result.rows) <= 10
            and x_axis
            and len(y_axis_cols) == 1
        ):
            return "pie", x_axis, y_axis_cols

        if x_axis and y_axis_cols:
            return "bar", x_axis, y_axis_cols

        return "table", x_axis, y_axis_cols

    def generate_chart_specification(
        self,
        *,
        natural_language_query: str,
        query_result: QueryResult,
        override_type: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Generate, validate, and transform query results into a ChartSpec.

        Raises
        ------
        ValidationError
            If chart specification fails validation or uses unsupported type.
        """
        if not query_result or not query_result.rows:
            raise ValidationError(
                message="Cannot generate chart for empty query result",
                detail="Query result contains 0 rows.",
            )

        chart_type_str, x_axis, y_axis_cols = self.select_chart_type(
            natural_language_query, query_result
        )

        if override_type:
            chart_type_str = override_type

        norm_type = chart_type_str.strip().lower()
        if norm_type not in SUPPORTED_V1_CHART_TYPES:
            raise ValidationError(
                message="Unsupported chart type",
                detail=f"Chart type '{chart_type_str}' is not supported in V1.",
            )

        display_title = title or self._derive_title(
            natural_language_query, norm_type, y_axis_cols
        )

        if norm_type == "table":
            spec = ChartSpec(
                type="table",
                title=display_title,
                x_axis=x_axis,
                y_axis=y_axis_cols[0] if y_axis_cols else None,
                data=query_result.rows,
                labels=[c.name for c in query_result.columns],
                metadata={"row_count": query_result.row_count},
            )
            return spec.model_dump()

        domain_chart_type = ChartType.from_str(norm_type)

        first_y = y_axis_cols or (
            [query_result.columns[1].name]
            if len(query_result.columns) > 1
            else [query_result.columns[0].name]
        )

        config = ChartConfiguration(
            chart_type=domain_chart_type,
            x_axis_column=x_axis,
            y_axis_columns=first_y,
            aggregation=AggregationType.NONE,
            title=display_title,
        )

        try:
            built_chart = self._chart_service.generate_chart(query_result, config)
            formatted = self._chart_service.format_chart(built_chart)
        except ChartValidationError as exc:
            raise ValidationError(
                message="Chart validation failed",
                detail=str(exc),
            ) from exc

        raw_spec = {
            "type": self._normalize_type_for_spec(norm_type),
            "title": display_title,
            "x_axis": x_axis,
            "y_axis": y_axis_cols[0] if len(y_axis_cols) == 1 else y_axis_cols,
            "data": query_result.rows,
            "series": formatted.get("series"),
            "labels": formatted.get("labels"),
            "metadata": {
                **formatted.get("metadata", {}),
                "statistics": formatted.get("statistics", {}),
                "recommended_colors": formatted.get("recommended_colors", []),
            },
        }

        try:
            validated_spec = ChartSpec.model_validate(raw_spec)
            return validated_spec.model_dump()
        except Exception as exc:
            raise ValidationError(
                message="Malformed chart JSON specification",
                detail=str(exc),
            ) from exc

    @staticmethod
    def _normalize_type_for_spec(chart_type_str: str) -> str:
        """Normalize internal enum strings to short V1 spec names."""
        mapping = {
            "line_chart": "line",
            "bar_chart": "bar",
            "area_chart": "area",
            "pie_chart": "pie",
        }
        return mapping.get(chart_type_str, chart_type_str)

    @staticmethod
    def _derive_title(nl_query: str, _chart_type: str, y_cols: list[str]) -> str:
        """Derive a clean human-readable chart title from user query."""
        clean = nl_query.strip().rstrip("?.!")
        if len(clean) <= 60:
            return clean[0].upper() + clean[1:]
        if y_cols:
            y_str = ", ".join(c.replace("_", " ").title() for c in y_cols)
            return f"{y_str} by Dimension"
        return "Query Result Visualization"
