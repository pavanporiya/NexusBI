"""Domain Enumerations for NexusBI backend.

Provides strongly-typed string-inherited enums for data sources, object types,
report types, and output formats.
"""

from __future__ import annotations

from enum import StrEnum


class DatasetSourceType(StrEnum):
    """Supported dataset data source types."""

    SNOWFLAKE = "snowflake"
    POSTGRES = "postgres"
    PG = "pg"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    REDSHIFT = "redshift"
    BIGQUERY = "bigquery"
    CSV = "csv"
    CUSTOM = "custom"


class DatasetObjectType(StrEnum):
    """Dataset object structural classification."""

    TABLE = "table"
    VIEW = "view"
    QUERY = "query"


class ReportType(StrEnum):
    """Analytical report structure types."""

    TABULAR = "tabular"
    CHART = "chart"
    SUMMARY = "summary"
    PIVOT = "pivot"
    CUSTOM = "custom"


class OutputFormat(StrEnum):
    """Supported report output and export formats."""

    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"


class WidgetType(StrEnum):
    """Supported dashboard widget visualization types."""

    KPI = "kpi"
    TABLE = "table"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    DONUT_CHART = "donut_chart"
    METRIC = "metric"
    TEXT = "text"

    @classmethod
    def from_str(cls, val: str | WidgetType) -> WidgetType:
        """Parse string or enum into a valid WidgetType instance."""
        if isinstance(val, cls):
            return val
        if not isinstance(val, str):
            raise ValueError(f"Invalid widget type: {val}")
        normalized = val.strip().lower()
        for member in cls:
            if member.value == normalized or member.name.lower() == normalized:
                return member
        raise ValueError(f"Invalid widget type: {val}")


class ChartType(StrEnum):
    """Supported chart engine visualization types."""

    KPI = "kpi"
    TABLE = "table"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    DONUT_CHART = "donut_chart"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    TREEMAP = "treemap"
    FUNNEL = "funnel"
    SANKEY = "sankey"

    @classmethod
    def from_str(cls, val: str | ChartType) -> ChartType:
        """Parse string or enum into a valid ChartType instance."""
        if isinstance(val, cls):
            return val
        if not isinstance(val, str):
            raise ValueError(f"Invalid chart type: {val}")
        normalized = val.strip().lower()
        alias_map = {
            "line": cls.LINE_CHART,
            "bar": cls.BAR_CHART,
            "area": cls.AREA_CHART,
            "pie": cls.PIE_CHART,
            "donut": cls.DONUT_CHART,
            "kpi": cls.KPI,
            "table": cls.TABLE,
        }
        if normalized in alias_map:
            return alias_map[normalized]
        for member in cls:
            if member.value == normalized or member.name.lower() == normalized:
                return member
        raise ValueError(f"Invalid chart type: {val}")


class AxisType(StrEnum):
    """Chart axis classification type."""

    X = "x"
    Y = "y"
    CATEGORY = "category"
    NUMERIC = "numeric"
    TIME = "time"
    SERIES = "series"

    @classmethod
    def from_str(cls, val: str | AxisType) -> AxisType:
        """Parse string or enum into a valid AxisType instance."""
        if isinstance(val, cls):
            return val
        if not isinstance(val, str):
            raise ValueError(f"Invalid axis type: {val}")
        normalized = val.strip().lower()
        for member in cls:
            if member.value == normalized or member.name.lower() == normalized:
                return member
        raise ValueError(f"Invalid axis type: {val}")


class AggregationType(StrEnum):
    """Aggregation operations for chart value computing."""

    SUM = "sum"
    AVG = "avg"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    NONE = "none"

    @classmethod
    def from_str(cls, val: str | AggregationType) -> AggregationType:
        """Parse string or enum into a valid AggregationType instance."""
        if isinstance(val, cls):
            return val
        if not isinstance(val, str):
            raise ValueError(f"Invalid aggregation type: {val}")
        normalized = val.strip().lower()
        for member in cls:
            if member.value == normalized or member.name.lower() == normalized:
                return member
        raise ValueError(f"Invalid aggregation type: {val}")
