"""Comprehensive unit tests for Report Management use cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.dto.report_dto import (
    CreateReportDTO,
    UpdateReportDTO,
)
from app.application.use_cases.create_report import CreateReportUseCase
from app.application.use_cases.delete_report import DeleteReportUseCase
from app.application.use_cases.get_report import GetReportUseCase
from app.application.use_cases.list_reports import ListReportsUseCase
from app.application.use_cases.update_report import UpdateReportUseCase
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.dataset import Dataset
from app.domain.entities.report import Report
from app.domain.value_objects.filter_params import FilterParams


@pytest.fixture
def mock_report_repo() -> MagicMock:
    """Mock IReportRepository."""
    return MagicMock()


@pytest.fixture
def mock_dataset_repo() -> MagicMock:
    """Mock IDatasetRepository."""
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = Dataset(
        id="ds-valid",
        name="Valid Dataset",
        source_type="postgres",
        query_or_table="public.table",
        owner_id="usr-1",
    )
    return mock_repo


def test_create_report_use_case_success(
    mock_report_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Create report succeeds when dataset exists."""
    saved_report = Report(
        id="rep-created",
        name="Created Report",
        dataset_id="ds-valid",
        owner_id="usr-1",
        report_type="tabular",
        output_format="csv",
        description="Desc",
        schedule="0 0 * * *",
        is_active=True,
    )
    mock_report_repo.save.return_value = saved_report

    use_case = CreateReportUseCase(
        report_repository=mock_report_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = CreateReportDTO(
        name="Created Report",
        dataset_id="ds-valid",
        report_type="tabular",
        output_format="csv",
        description="Desc",
        schedule="0 0 * * *",
    )

    result = use_case.execute(dto, owner_id="usr-1")

    assert result.id == "rep-created"
    assert result.name == "Created Report"
    assert result.owner_id == "usr-1"
    assert result.dataset_id == "ds-valid"
    assert result.report_type == "tabular"
    assert result.output_format == "csv"
    mock_dataset_repo.get_by_id.assert_called_once_with("ds-valid")
    mock_report_repo.save.assert_called_once()


def test_create_report_use_case_dataset_not_found(
    mock_report_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Create report raises EntityNotFoundError if referenced dataset is missing."""
    mock_dataset_repo.get_by_id.return_value = None

    use_case = CreateReportUseCase(
        report_repository=mock_report_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = CreateReportDTO(
        name="Created Report",
        dataset_id="ds-missing",
    )

    with pytest.raises(EntityNotFoundError, match="Dataset not found"):
        use_case.execute(dto, owner_id="usr-1")


def test_update_report_use_case_success(
    mock_report_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Update report succeeds and verifies new dataset_id if provided."""
    existing = Report(
        id="rep-1",
        name="Original",
        dataset_id="ds-valid",
        owner_id="usr-1",
    )
    mock_report_repo.get_by_id.return_value = existing
    mock_report_repo.save.return_value = existing

    use_case = UpdateReportUseCase(
        report_repository=mock_report_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = UpdateReportDTO(
        name="Updated Name", dataset_id="ds-valid", report_type="chart"
    )

    result = use_case.execute("rep-1", dto)

    assert result.name == "Updated Name"
    assert result.report_type == "chart"
    mock_report_repo.save.assert_called_once()


def test_update_report_use_case_dataset_not_found(
    mock_report_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Update report raises EntityNotFoundError if new dataset_id is missing."""
    existing = Report(
        id="rep-1",
        name="Original",
        dataset_id="ds-valid",
        owner_id="usr-1",
    )
    mock_report_repo.get_by_id.return_value = existing
    mock_dataset_repo.get_by_id.return_value = None

    use_case = UpdateReportUseCase(
        report_repository=mock_report_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = UpdateReportDTO(dataset_id="ds-non-existent")

    with pytest.raises(EntityNotFoundError, match="Dataset not found"):
        use_case.execute("rep-1", dto)


def test_get_and_delete_report_use_cases(
    mock_report_repo: MagicMock,
) -> None:
    """Test GetReportUseCase and DeleteReportUseCase."""
    report = Report(
        id="rep-1",
        name="Report",
        dataset_id="ds-1",
        owner_id="usr-1",
    )
    mock_report_repo.get_by_id.return_value = report
    mock_report_repo.delete.return_value = True

    get_uc = GetReportUseCase(mock_report_repo)
    get_res = get_uc.execute("rep-1")
    assert get_res.id == "rep-1"

    del_uc = DeleteReportUseCase(mock_report_repo)
    del_uc.execute("rep-1")
    mock_report_repo.delete.assert_called_once_with("rep-1")


def test_list_reports_use_case(
    mock_report_repo: MagicMock,
) -> None:
    """Test ListReportsUseCase pagination wrapping."""
    report = Report(
        id="rep-1",
        name="Report",
        dataset_id="ds-1",
        owner_id="usr-1",
    )
    mock_report_repo.list.return_value = ([report], 1)

    use_case = ListReportsUseCase(mock_report_repo)
    res = use_case.execute(FilterParams(page=1, page_size=20))

    assert res.total == 1
    assert res.page == 1
    assert res.items[0].id == "rep-1"
