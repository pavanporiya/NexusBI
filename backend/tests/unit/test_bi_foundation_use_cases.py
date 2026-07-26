"""Unit tests for BI Foundation application use cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.dto.dashboard_dto import (
    CreateDashboardDTO,
    UpdateDashboardDTO,
)
from app.application.dto.dataset_dto import (
    CreateDatasetDTO,
    UpdateDatasetDTO,
)
from app.application.dto.report_dto import (
    CreateReportDTO,
    UpdateReportDTO,
)
from app.application.use_cases.create_dashboard import CreateDashboardUseCase
from app.application.use_cases.create_dataset import CreateDatasetUseCase
from app.application.use_cases.create_report import CreateReportUseCase
from app.application.use_cases.delete_dashboard import DeleteDashboardUseCase
from app.application.use_cases.delete_dataset import DeleteDatasetUseCase
from app.application.use_cases.delete_report import DeleteReportUseCase
from app.application.use_cases.get_dashboard import GetDashboardUseCase
from app.application.use_cases.get_dataset import GetDatasetUseCase
from app.application.use_cases.get_report import GetReportUseCase
from app.application.use_cases.list_dashboards import ListDashboardsUseCase
from app.application.use_cases.list_datasets import ListDatasetsUseCase
from app.application.use_cases.list_reports import ListReportsUseCase
from app.application.use_cases.update_dashboard import UpdateDashboardUseCase
from app.application.use_cases.update_dataset import UpdateDatasetUseCase
from app.application.use_cases.update_report import UpdateReportUseCase
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.entities.report import Report
from app.domain.value_objects.filter_params import FilterParams


def test_dashboard_use_cases() -> None:
    """Test Dashboard CRUD and List use cases."""
    repo = MagicMock()
    dataset_repo = MagicMock()
    dataset = Dataset(
        id="ds-1",
        name="DS1",
        source_type="postgres",
        query_or_table="tbl",
        owner_id="u-1",
    )
    dataset_repo.get_by_id.return_value = dataset

    dashboard = Dashboard(
        id="dash-1",
        name="Executive",
        owner_id="u-1",
        dataset_id="ds-1",
        description="Desc",
    )
    repo.save.return_value = dashboard
    repo.get_by_id.return_value = dashboard
    repo.delete.return_value = True
    repo.list.return_value = ([dashboard], 1)

    # 1. Create
    create_uc = CreateDashboardUseCase(
        dashboard_repository=repo, dataset_repository=dataset_repo
    )
    dto = create_uc.execute(
        CreateDashboardDTO(name="Executive", dataset_id="ds-1", description="Desc"),
        owner_id="u-1",
    )
    assert dto.name == "Executive"
    assert dto.owner_id == "u-1"
    assert dto.dataset_id == "ds-1"

    # 2. Get
    get_uc = GetDashboardUseCase(repo)
    get_dto = get_uc.execute("dash-1")
    assert get_dto.id == "dash-1"

    # 3. Update
    update_uc = UpdateDashboardUseCase(
        dashboard_repository=repo, dataset_repository=dataset_repo
    )
    up_dto = update_uc.execute("dash-1", UpdateDashboardDTO(name="New Name"))
    assert up_dto.name == "New Name"

    # 4. List
    list_uc = ListDashboardsUseCase(repo)
    paginated = list_uc.execute(FilterParams(page=1, page_size=10))
    assert paginated.total == 1
    assert len(paginated.items) == 1
    assert paginated.total_pages == 1

    # 5. Delete
    delete_uc = DeleteDashboardUseCase(repo)
    delete_uc.execute("dash-1")
    repo.delete.assert_called_with("dash-1")

    # NotFound errors
    repo.get_by_id.return_value = None
    with pytest.raises(EntityNotFoundError):
        get_uc.execute("invalid-id")

    repo.delete.return_value = False
    with pytest.raises(EntityNotFoundError):
        delete_uc.execute("invalid-id")


def test_report_use_cases() -> None:
    """Test Report CRUD and List use cases."""
    repo = MagicMock()
    dataset_repo = MagicMock()
    dataset_repo.get_by_id.return_value = Dataset(
        id="ds-1",
        name="DS1",
        source_type="postgres",
        query_or_table="tbl",
        owner_id="u-1",
    )
    report = Report(
        id="rep-1",
        name="Sales",
        dataset_id="ds-1",
        query="SELECT * FROM sales",
        owner_id="u-1",
    )
    repo.save.return_value = report
    repo.get_by_id.return_value = report
    repo.delete.return_value = True
    repo.list.return_value = ([report], 1)

    create_uc = CreateReportUseCase(
        report_repository=repo, dataset_repository=dataset_repo
    )
    dto = create_uc.execute(
        CreateReportDTO(name="Sales", dataset_id="ds-1", query="SELECT * FROM sales"),
        owner_id="u-1",
    )
    assert dto.name == "Sales"
    assert dto.dataset_id == "ds-1"

    get_uc = GetReportUseCase(repo)
    assert get_uc.execute("rep-1").id == "rep-1"

    update_uc = UpdateReportUseCase(
        report_repository=repo, dataset_repository=dataset_repo
    )
    assert update_uc.execute("rep-1", UpdateReportDTO(name="Sales 2")).id == "rep-1"

    list_uc = ListReportsUseCase(repo)
    paginated = list_uc.execute(FilterParams())
    assert paginated.total == 1

    delete_uc = DeleteReportUseCase(repo)
    delete_uc.execute("rep-1")
    repo.delete.assert_called_with("rep-1")


def test_dataset_use_cases() -> None:
    """Test Dataset CRUD and List use cases."""
    repo = MagicMock()
    dataset = Dataset(
        id="ds-1",
        name="Orders",
        source_type="postgres",
        query_or_table="orders",
        owner_id="u-1",
    )
    repo.save.return_value = dataset
    repo.get_by_id.return_value = dataset
    repo.delete.return_value = True
    repo.list.return_value = ([dataset], 1)

    create_uc = CreateDatasetUseCase(repo)
    dto = create_uc.execute(
        CreateDatasetDTO(
            name="Orders", source_type="postgres", query_or_table="orders"
        ),
        owner_id="u-1",
    )
    assert dto.name == "Orders"

    get_uc = GetDatasetUseCase(repo)
    assert get_uc.execute("ds-1").id == "ds-1"

    update_uc = UpdateDatasetUseCase(repo)
    assert update_uc.execute("ds-1", UpdateDatasetDTO(name="New Orders")).id == "ds-1"

    list_uc = ListDatasetsUseCase(repo)
    paginated = list_uc.execute(FilterParams())
    assert paginated.total == 1

    delete_uc = DeleteDatasetUseCase(repo)
    delete_uc.execute("ds-1")
    repo.delete.assert_called_with("ds-1")
