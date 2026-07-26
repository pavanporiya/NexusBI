"""Unit tests for domain enums."""

from app.domain.enums import (
    DatasetObjectType,
    DatasetSourceType,
    OutputFormat,
    ReportType,
)


def test_dataset_source_type_enum() -> None:
    """Test DatasetSourceType enum members and string equality."""
    assert DatasetSourceType.SNOWFLAKE.value == "snowflake"
    assert DatasetSourceType.POSTGRES.value == "postgres"
    assert DatasetSourceType.CSV.value == "csv"
    assert DatasetSourceType.CUSTOM.value == "custom"
    assert isinstance(DatasetSourceType.SNOWFLAKE, str)


def test_dataset_object_type_enum() -> None:
    """Test DatasetObjectType enum members and string equality."""
    assert DatasetObjectType.TABLE.value == "table"
    assert DatasetObjectType.VIEW.value == "view"
    assert DatasetObjectType.QUERY.value == "query"
    assert isinstance(DatasetObjectType.TABLE, str)


def test_report_type_enum() -> None:
    """Test ReportType enum members and string equality."""
    assert ReportType.TABULAR.value == "tabular"
    assert ReportType.CHART.value == "chart"
    assert ReportType.SUMMARY.value == "summary"
    assert ReportType.PIVOT.value == "pivot"
    assert ReportType.CUSTOM.value == "custom"
    assert isinstance(ReportType.TABULAR, str)


def test_output_format_enum() -> None:
    """Test OutputFormat enum members and string equality."""
    assert OutputFormat.JSON.value == "json"
    assert OutputFormat.CSV.value == "csv"
    assert OutputFormat.PDF.value == "pdf"
    assert OutputFormat.EXCEL.value == "excel"
    assert OutputFormat.HTML.value == "html"
    assert isinstance(OutputFormat.JSON, str)
