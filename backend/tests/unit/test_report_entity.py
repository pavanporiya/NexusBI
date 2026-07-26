"""Unit tests for Report domain entity."""

from __future__ import annotations

import pytest

from app.domain.entities.report import Report
from app.domain.enums import OutputFormat, ReportType
from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.schedule import Schedule


def test_report_entity_creation_valid() -> None:
    """Test creating a Report entity with valid parameters."""
    report = Report(
        id="rep-123",
        name="  Quarterly Revenue  ",
        dataset_id="  ds-456  ",
        owner_id="  user-789  ",
        report_type="tabular",
        output_format="csv",
        description="Revenue breakdown for Q3",
        schedule="0 0 * * *",
        is_active=True,
    )
    assert report.id == "rep-123"
    assert report.name == "Quarterly Revenue"
    assert report.dataset_id == "ds-456"
    assert report.owner_id == "user-789"
    assert report.report_type == ReportType.TABULAR
    assert report.output_format == OutputFormat.CSV
    assert report.description == "Revenue breakdown for Q3"
    assert report.schedule == Schedule("0 0 * * *")
    assert report.schedule_str == "0 0 * * *"
    assert report.is_active is True


def test_report_entity_validation_empty_name() -> None:
    """Test Report validation failure on empty name."""
    with pytest.raises(DomainValidationError, match="Report name must not be empty"):
        Report(
            id="r-1",
            name="   ",
            dataset_id="ds-1",
            owner_id="u-1",
        )


def test_report_entity_validation_empty_dataset() -> None:
    """Test Report validation failure on empty dataset_id."""
    with pytest.raises(
        DomainValidationError, match="Report dataset_id must not be empty"
    ):
        Report(
            id="r-1",
            name="Valid Report",
            dataset_id="  ",
            owner_id="u-1",
        )


def test_report_entity_validation_empty_owner() -> None:
    """Test Report validation failure on empty owner_id."""
    with pytest.raises(
        DomainValidationError, match="Report owner_id must not be empty"
    ):
        Report(
            id="r-1",
            name="Valid Report",
            dataset_id="ds-1",
            owner_id="",
        )


def test_report_entity_validation_invalid_report_type() -> None:
    """Test Report validation failure on invalid report_type."""
    with pytest.raises(
        DomainValidationError, match="Invalid report_type 'invalid_type'"
    ):
        Report(
            id="r-1",
            name="Valid Report",
            dataset_id="ds-1",
            owner_id="u-1",
            report_type="invalid_type",
        )


def test_report_entity_validation_invalid_output_format() -> None:
    """Test Report validation failure on invalid output_format."""
    with pytest.raises(DomainValidationError, match="Invalid output_format 'docx'"):
        Report(
            id="r-1",
            name="Valid Report",
            dataset_id="ds-1",
            owner_id="u-1",
            output_format="docx",
        )


def test_report_entity_validation_invalid_schedule() -> None:
    """Test Report validation failure on invalid cron schedule."""
    with pytest.raises(DomainValidationError, match="Invalid cron expression"):
        Report(
            id="r-1",
            name="Valid Report",
            dataset_id="ds-1",
            owner_id="u-1",
            schedule="invalid cron spec",
        )


def test_report_entity_update() -> None:
    """Test Report update method."""
    report = Report(
        id="r-1",
        name="Old Name",
        dataset_id="ds-1",
        owner_id="u-1",
        report_type="tabular",
        output_format="json",
    )
    old_updated_at = report.updated_at

    report.update(
        name="  New Name  ",
        description="  New Description  ",
        dataset_id="ds-2",
        report_type="chart",
        output_format="pdf",
        schedule="0 12 * * 1",
        is_active=False,
    )

    assert report.name == "New Name"
    assert report.description == "New Description"
    assert report.dataset_id == "ds-2"
    assert report.report_type == ReportType.CHART
    assert report.output_format == OutputFormat.PDF
    assert report.schedule == Schedule("0 12 * * 1")
    assert report.schedule_str == "0 12 * * 1"
    assert report.is_active is False
    assert report.updated_at >= old_updated_at


def test_report_entity_update_validation_failures() -> None:
    """Test Report update validation failures."""
    report = Report(
        id="r-1",
        name="Valid Report",
        dataset_id="ds-1",
        owner_id="u-1",
    )
    with pytest.raises(DomainValidationError, match="Report name must not be empty"):
        report.update(name="   ")

    with pytest.raises(
        DomainValidationError, match="Report dataset_id must not be empty"
    ):
        report.update(dataset_id="")

    with pytest.raises(
        DomainValidationError, match="Invalid report_type 'unsupported'"
    ):
        report.update(report_type="unsupported")
