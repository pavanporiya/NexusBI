"""Unit tests for chart builder strategies."""

from __future__ import annotations

import pytest

from app.domain.enums import AggregationType, ChartType
from app.domain.value_objects.chart import ChartConfiguration
from app.domain.value_objects.query import (
    QueryColumn,
    QueryMetadata,
    QueryResult,
    QueryStatistics,
)
from app.infrastructure.chart.builders.area_chart_builder import AreaChartBuilder
from app.infrastructure.chart.builders.bar_chart_builder import BarChartBuilder
from app.infrastructure.chart.builders.donut_chart_builder import DonutChartBuilder
from app.infrastructure.chart.builders.kpi_card_builder import KPICardBuilder
from app.infrastructure.chart.builders.line_chart_builder import LineChartBuilder
from app.infrastructure.chart.builders.pie_chart_builder import PieChartBuilder
from app.infrastructure.chart.builders.table_builder import TableBuilder


def make_query_result() -> QueryResult:
    """Build a shared query result fixture for builder tests."""
    columns = [
        QueryColumn(name="month", type="string"),
        QueryColumn(name="sales", type="integer"),
        QueryColumn(name="profit", type="integer"),
        QueryColumn(name="segment", type="string"),
    ]
    rows = [
        {"month": "Jan", "sales": 10, "profit": 2, "segment": "Retail"},
        {"month": "Feb", "sales": 12, "profit": 3, "segment": "Retail"},
        {"month": "Jan", "sales": 8, "profit": 1, "segment": "Enterprise"},
        {"month": "Feb", "sales": 15, "profit": 4, "segment": "Enterprise"},
    ]
    return QueryResult(
        rows=rows,
        columns=columns,
        column_types={column.name: column.type for column in columns},
        execution_time=0.01,
        row_count=len(rows),
        metadata=QueryMetadata(
            statistics=QueryStatistics(rows_scanned=len(rows)),
            execution_time=0.01,
            row_count=len(rows),
            columns=columns,
        ),
    )


def test_kpi_builder_returns_scalar_metric() -> None:
    builder = KPICardBuilder()
    config = ChartConfiguration(
        chart_type=ChartType.KPI,
        y_axis_columns=["sales"],
        aggregation=AggregationType.SUM,
    )

    result = builder.build(make_query_result(), config)

    assert result.title == "KPI (sales)"
    assert result.metadata["kpi_value"] == 45
    assert result.series[0].data[0].y == 45
    assert result.statistics["sum"] == 45


def test_table_builder_preserves_all_columns() -> None:
    builder = TableBuilder()
    config = ChartConfiguration(chart_type=ChartType.TABLE, title="Rows")

    result = builder.build(make_query_result(), config)

    assert result.title == "Rows"
    assert result.labels == ["month", "sales", "profit", "segment"]
    assert len(result.series) == 4
    assert [point.value for point in result.series[0].data] == [
        "Jan",
        "Feb",
        "Jan",
        "Feb",
    ]


def test_bar_builder_supports_multiple_series() -> None:
    builder = BarChartBuilder()
    config = ChartConfiguration(
        chart_type=ChartType.BAR_CHART,
        x_axis_column="month",
        y_axis_columns=["sales", "profit"],
        aggregation=AggregationType.SUM,
    )

    result = builder.build(make_query_result(), config)

    assert result.labels == ["Jan", "Feb"]
    assert [series.name for series in result.series] == ["sales", "profit"]
    assert [point.y for point in result.series[0].data] == [18, 27]
    assert [point.y for point in result.series[1].data] == [3, 7]


def test_line_builder_supports_grouped_series() -> None:
    builder = LineChartBuilder()
    config = ChartConfiguration(
        chart_type=ChartType.LINE_CHART,
        x_axis_column="month",
        y_axis_columns=["sales"],
        group_by_column="segment",
        aggregation=AggregationType.SUM,
    )

    result = builder.build(make_query_result(), config)

    assert result.labels == ["Jan", "Feb"]
    assert [series.name for series in result.series] == ["Retail", "Enterprise"]
    assert [point.y for point in result.series[0].data] == [10, 12]
    assert [point.y for point in result.series[1].data] == [8, 15]


def test_pie_builder_aggregates_by_category() -> None:
    builder = PieChartBuilder()
    config = ChartConfiguration(
        chart_type=ChartType.PIE_CHART,
        x_axis_column="month",
        y_axis_columns=["sales"],
        aggregation=AggregationType.SUM,
    )

    result = builder.build(make_query_result(), config)

    assert result.labels == ["Jan", "Feb"]
    assert result.series[0].name == "sales"
    assert [point.y for point in result.series[0].data] == [18, 27]
    assert result.metadata["slice_count"] == 2


def test_area_builder_supports_multiple_series() -> None:
    builder = AreaChartBuilder()
    config = ChartConfiguration(
        chart_type=ChartType.AREA_CHART,
        x_axis_column="month",
        y_axis_columns=["sales", "profit"],
        aggregation=AggregationType.SUM,
    )

    result = builder.build(make_query_result(), config)

    assert result.labels == ["Jan", "Feb"]
    assert len(result.series) == 2
    assert [point.y for point in result.series[0].data] == [18, 27]
    assert [point.y for point in result.series[1].data] == [3, 7]


def test_donut_builder_returns_slice_metadata() -> None:
    builder = DonutChartBuilder()
    config = ChartConfiguration(
        chart_type=ChartType.DONUT_CHART,
        x_axis_column="month",
        y_axis_columns=["profit"],
        aggregation=AggregationType.SUM,
    )

    result = builder.build(make_query_result(), config)

    assert result.labels == ["Jan", "Feb"]
    assert result.metadata["inner_radius"] == 0.6
    assert [point.y for point in result.series[0].data] == [3, 7]
    assert all("color" in point.metadata for point in result.series[0].data)


@pytest.mark.parametrize(
    ("builder", "chart_type"),
    [
        (KPICardBuilder(), ChartType.KPI),
        (TableBuilder(), ChartType.TABLE),
        (BarChartBuilder(), ChartType.BAR_CHART),
        (LineChartBuilder(), ChartType.LINE_CHART),
        (PieChartBuilder(), ChartType.PIE_CHART),
        (AreaChartBuilder(), ChartType.AREA_CHART),
        (DonutChartBuilder(), ChartType.DONUT_CHART),
    ],
)
def test_each_builder_exposes_supported_chart_type(
    builder: (
        KPICardBuilder
        | TableBuilder
        | BarChartBuilder
        | LineChartBuilder
        | PieChartBuilder
        | AreaChartBuilder
        | DonutChartBuilder
    ),
    chart_type: ChartType,
) -> None:
    assert builder.chart_type is chart_type
