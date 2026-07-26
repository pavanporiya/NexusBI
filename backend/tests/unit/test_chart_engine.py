"""Unit tests for chart value objects, validator, formatter, registry, and service."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from app.application.interfaces import (
    IChartBuilder,
    IChartFormatter,
    IChartValidator,
)
from app.application.services.chart_service import ChartService
from app.domain.enums import AggregationType, AxisType, ChartType
from app.domain.exceptions import ChartValidationError
from app.domain.value_objects.chart import (
    Axis,
    Chart,
    ChartConfiguration,
    ChartPoint,
    ChartResult,
    ChartSeries,
    ColorPalette,
    Legend,
)
from app.domain.value_objects.query import (
    QueryColumn,
    QueryMetadata,
    QueryResult,
    QueryStatistics,
)
from app.infrastructure.chart.builders.bar_chart_builder import BarChartBuilder
from app.infrastructure.chart.formatter import DefaultChartFormatter
from app.infrastructure.chart.registry import ChartBuilderRegistry
from app.infrastructure.chart.validator import DefaultChartValidator


def make_query_result(
    rows: list[dict[str, object]] | None = None,
    columns: list[QueryColumn] | None = None,
) -> QueryResult:
    """Build a reusable query result fixture."""
    if rows is None:
        rows = [
            {"category": "Jan", "sales": 10, "profit": 2, "segment": "A"},
            {"category": "Feb", "sales": 15, "profit": 4, "segment": "B"},
            {"category": "Jan", "sales": 5, "profit": 1, "segment": "A"},
        ]
    columns = columns or [
        QueryColumn(name="category", type="string"),
        QueryColumn(name="sales", type="integer"),
        QueryColumn(name="profit", type="integer"),
        QueryColumn(name="segment", type="string"),
    ]
    metadata = QueryMetadata(
        statistics=QueryStatistics(query_plan="SELECT ...", rows_scanned=len(rows)),
        execution_time=0.02,
        row_count=len(rows),
        columns=columns,
    )
    return QueryResult(
        rows=rows,
        columns=columns,
        column_types={column.name: column.type for column in columns},
        execution_time=0.02,
        row_count=len(rows),
        metadata=metadata,
    )


def make_config(
    chart_type: ChartType = ChartType.BAR_CHART,
    x_axis_column: str | None = "category",
    y_axis_columns: list[str] | None = None,
    group_by_column: str | None = None,
    aggregation: AggregationType = AggregationType.SUM,
    title: str | None = None,
    subtitle: str | None = None,
    metadata: dict[str, Any] | None = None,
    color_palette: ColorPalette | str | None = None,
) -> ChartConfiguration:
    """Build a reusable chart configuration fixture."""
    return ChartConfiguration(
        chart_type=chart_type,
        x_axis_column=x_axis_column,
        y_axis_columns=["sales"] if y_axis_columns is None else y_axis_columns,
        group_by_column=group_by_column,
        aggregation=aggregation,
        title=title,
        subtitle=subtitle,
        color_palette=color_palette or ColorPalette(),
        metadata=metadata or {"source": "tests"},
    )


def make_chart_result() -> ChartResult:
    """Build a reusable chart result fixture."""
    point = ChartPoint(x="Jan", y=10, label="January", value=10, metadata={"row": 1})
    series = ChartSeries(
        name="sales",
        data=[point],
        color="#123456",
        chart_type=ChartType.BAR_CHART,
        metadata={"unit": "USD"},
    )
    return ChartResult(
        title="Revenue",
        subtitle="Monthly",
        labels=["Jan"],
        series=[series],
        metadata={"chart_type": "bar_chart"},
        statistics={"sum": 10, "count": 1},
        recommended_colors=["#123456"],
    )


def test_chart_point_preserves_values() -> None:
    point = ChartPoint(x="A", y=9, label="Alpha", value=9, metadata={"ok": True})

    assert point.x == "A"
    assert point.y == 9
    assert point.label == "Alpha"
    assert point.value == 9
    assert point.metadata == {"ok": True}


def test_chart_series_strips_name() -> None:
    series = ChartSeries(name=" sales ", data=[])

    assert series.name == "sales"


def test_chart_series_rejects_blank_name() -> None:
    with pytest.raises(ChartValidationError, match="must not be empty"):
        ChartSeries(name="   ")


def test_axis_normalizes_name() -> None:
    axis = Axis(name=" category ", title="Category", type=AxisType.X)

    assert axis.name == "category"


def test_axis_rejects_blank_name() -> None:
    with pytest.raises(ChartValidationError, match="must not be empty"):
        Axis(name="")


def test_legend_defaults() -> None:
    legend = Legend()

    assert legend.show is True
    assert legend.position == "top"
    assert legend.labels == []


def test_color_palette_falls_back_to_default_colors() -> None:
    palette = ColorPalette(name="custom", colors=[])

    assert palette.name == "custom"
    assert len(palette.colors) >= 1


def test_chart_configuration_normalizes_types() -> None:
    config = ChartConfiguration(
        chart_type=cast(Any, "bar_chart"),
        x_axis_column="category",
        y_axis_columns=["sales"],
        aggregation=cast(Any, "sum"),
        color_palette="brand",
    )

    assert config.chart_type is ChartType.BAR_CHART
    assert config.aggregation is AggregationType.SUM
    assert isinstance(config.color_palette, ColorPalette)
    assert config.color_palette.name == "brand"


def test_chart_requires_non_empty_title() -> None:
    with pytest.raises(ChartValidationError, match="must not be empty"):
        Chart(
            title=" ",
            chart_type=ChartType.BAR_CHART,
            config=make_config(),
        )


def test_chart_result_holds_structured_output() -> None:
    result = make_chart_result()

    assert result.title == "Revenue"
    assert result.labels == ["Jan"]
    assert result.series[0].metadata["unit"] == "USD"


@pytest.mark.parametrize(
    ("config_factory", "message"),
    [
        (
            lambda: make_config(chart_type=cast(Any, "scatter")),
            "Invalid chart type",
        ),
        (
            lambda: make_config(x_axis_column=None),
            "X-axis column is required",
        ),
        (
            lambda: make_config(y_axis_columns=[]),
            "Y-axis metric column",
        ),
        (
            lambda: make_config(y_axis_columns=["sales", "sales"]),
            "Duplicate series columns",
        ),
        (
            lambda: make_config(aggregation=cast(Any, "bogus")),
            "Invalid aggregation type",
        ),
    ],
)
def test_validator_rejects_invalid_configuration(
    config_factory: Callable[[], ChartConfiguration], message: str
) -> None:
    validator = DefaultChartValidator()

    with pytest.raises(ChartValidationError, match=message):
        validator.validate(
            make_query_result(),
            config_factory(),
        )


def test_validator_rejects_empty_dataset() -> None:
    validator = DefaultChartValidator()
    result = make_query_result(rows=[])

    with pytest.raises(ChartValidationError, match="Dataset is empty"):
        validator.validate(result, make_config())


def test_validator_rejects_all_null_metric_values() -> None:
    validator = DefaultChartValidator()
    result = make_query_result(
        rows=[
            {"category": "Jan", "sales": None, "profit": 1, "segment": "A"},
            {"category": "Feb", "sales": None, "profit": 2, "segment": "B"},
        ]
    )

    with pytest.raises(ChartValidationError, match="contains only null values"):
        validator.validate(result, make_config())


def test_formatter_returns_api_shape() -> None:
    payload = DefaultChartFormatter().format(make_chart_result())

    assert payload["title"] == "Revenue"
    assert payload["subtitle"] == "Monthly"
    assert payload["labels"] == ["Jan"]
    assert payload["metadata"]["chart_type"] == "bar_chart"
    assert payload["statistics"]["sum"] == 10
    assert payload["recommended_colors"] == ["#123456"]
    assert payload["series"][0]["name"] == "sales"
    assert payload["series"][0]["chart_type"] == "bar_chart"
    assert payload["series"][0]["data"][0]["label"] == "January"
    assert payload["series"][0]["metadata"]["unit"] == "USD"


def test_registry_automatically_registers_all_builders() -> None:
    ChartBuilderRegistry.reset()

    supported = set(ChartBuilderRegistry.supported_types())

    assert supported == {
        ChartType.KPI,
        ChartType.TABLE,
        ChartType.BAR_CHART,
        ChartType.LINE_CHART,
        ChartType.PIE_CHART,
        ChartType.AREA_CHART,
        ChartType.DONUT_CHART,
    }
    assert isinstance(ChartBuilderRegistry.get(ChartType.BAR_CHART), BarChartBuilder)


def test_registry_rejects_unknown_chart_type() -> None:
    ChartBuilderRegistry.reset()

    with pytest.raises(ChartValidationError, match="Unsupported chart type"):
        ChartBuilderRegistry.get("unknown")


def test_chart_service_selects_builder_from_registry() -> None:
    validator = MagicMock(spec=IChartValidator)
    formatter = MagicMock(spec=IChartFormatter)
    builder = MagicMock(spec=IChartBuilder)
    expected = make_chart_result()
    builder.build.return_value = expected
    formatter.format.return_value = {"title": expected.title}

    service = ChartService(validator=validator, formatter=formatter)
    result = make_query_result()
    config = make_config()

    with patch.object(ChartBuilderRegistry, "get", return_value=builder) as mock_get:
        actual = service.generate_chart(result, config)
        assert actual is expected
        validator.validate.assert_called_once_with(result, config)
        mock_get.assert_called_once_with(config.chart_type)
        builder.build.assert_called_once_with(result, config)


def test_chart_service_validation_failure_payload() -> None:
    validator = MagicMock(spec=IChartValidator)
    validator.validate.side_effect = ChartValidationError("bad config")
    service = ChartService(
        validator=validator,
        formatter=MagicMock(spec=IChartFormatter),
    )

    payload = service.validate_chart(make_query_result(), make_config())

    assert payload == {
        "valid": False,
        "message": "bad config",
        "errors": ["bad config"],
    }


def test_chart_service_formatter_integration() -> None:
    service = ChartService(
        validator=MagicMock(spec=IChartValidator),
        formatter=DefaultChartFormatter(),
    )

    payload = service.format_chart(make_chart_result())

    assert payload["series"][0]["name"] == "sales"
    assert payload["metadata"]["chart_type"] == "bar_chart"
