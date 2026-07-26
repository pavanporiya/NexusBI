"""Comprehensive unit tests for Dashboard Management use cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.dto.dashboard_dto import (
    CreateDashboardDTO,
    UpdateDashboardDTO,
)
from app.application.use_cases.create_dashboard import CreateDashboardUseCase
from app.application.use_cases.delete_dashboard import DeleteDashboardUseCase
from app.application.use_cases.get_dashboard import GetDashboardUseCase
from app.application.use_cases.list_dashboards import ListDashboardsUseCase
from app.application.use_cases.update_dashboard import UpdateDashboardUseCase
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.value_objects.filter_params import FilterParams


@pytest.fixture
def mock_dashboard_repo() -> MagicMock:
    """Mock IDashboardRepository."""
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


def test_create_dashboard_use_case_success(
    mock_dashboard_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Create dashboard succeeds when dataset exists."""
    saved_dashboard = Dashboard(
        id="dash-created",
        name="Created Dashboard",
        owner_id="usr-1",
        dataset_id="ds-valid",
        description="Desc",
        layout_json={"widgets": []},
        is_public=True,
        is_active=True,
    )
    mock_dashboard_repo.save.return_value = saved_dashboard

    use_case = CreateDashboardUseCase(
        dashboard_repository=mock_dashboard_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = CreateDashboardDTO(
        name="Created Dashboard",
        dataset_id="ds-valid",
        description="Desc",
        layout_json={"widgets": []},
        is_public=True,
    )

    result = use_case.execute(dto, owner_id="usr-1")

    assert result.id == "dash-created"
    assert result.name == "Created Dashboard"
    assert result.owner_id == "usr-1"
    assert result.dataset_id == "ds-valid"
    mock_dataset_repo.get_by_id.assert_called_once_with("ds-valid")
    mock_dashboard_repo.save.assert_called_once()


def test_create_dashboard_use_case_dataset_not_found(
    mock_dashboard_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Create dashboard raises EntityNotFoundError if referenced dataset is missing."""
    mock_dataset_repo.get_by_id.return_value = None

    use_case = CreateDashboardUseCase(
        dashboard_repository=mock_dashboard_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = CreateDashboardDTO(
        name="Created Dashboard",
        dataset_id="ds-missing",
    )

    with pytest.raises(EntityNotFoundError, match="Dataset not found"):
        use_case.execute(dto, owner_id="usr-1")


def test_update_dashboard_use_case_success(
    mock_dashboard_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Update dashboard succeeds and verifies new dataset_id if provided."""
    existing = Dashboard(
        id="dash-1",
        name="Original",
        owner_id="usr-1",
        dataset_id="ds-valid",
    )
    mock_dashboard_repo.get_by_id.return_value = existing
    mock_dashboard_repo.save.return_value = existing

    use_case = UpdateDashboardUseCase(
        dashboard_repository=mock_dashboard_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = UpdateDashboardDTO(name="Updated Name", dataset_id="ds-valid")

    result = use_case.execute("dash-1", dto)

    assert result.name == "Updated Name"
    mock_dashboard_repo.save.assert_called_once()


def test_update_dashboard_use_case_dataset_not_found(
    mock_dashboard_repo: MagicMock,
    mock_dataset_repo: MagicMock,
) -> None:
    """Update dashboard raises EntityNotFoundError if new dataset_id is missing."""
    existing = Dashboard(
        id="dash-1",
        name="Original",
        owner_id="usr-1",
        dataset_id="ds-valid",
    )
    mock_dashboard_repo.get_by_id.return_value = existing
    mock_dataset_repo.get_by_id.return_value = None

    use_case = UpdateDashboardUseCase(
        dashboard_repository=mock_dashboard_repo,
        dataset_repository=mock_dataset_repo,
    )
    dto = UpdateDashboardDTO(dataset_id="ds-non-existent")

    with pytest.raises(EntityNotFoundError, match="Dataset not found"):
        use_case.execute("dash-1", dto)


def test_get_and_delete_dashboard_use_cases(
    mock_dashboard_repo: MagicMock,
) -> None:
    """Test GetDashboardUseCase and DeleteDashboardUseCase."""
    dashboard = Dashboard(
        id="dash-1",
        name="Dashboard",
        owner_id="usr-1",
        dataset_id="ds-1",
    )
    mock_dashboard_repo.get_by_id.return_value = dashboard
    mock_dashboard_repo.delete.return_value = True

    get_uc = GetDashboardUseCase(mock_dashboard_repo)
    get_res = get_uc.execute("dash-1")
    assert get_res.id == "dash-1"

    del_uc = DeleteDashboardUseCase(mock_dashboard_repo)
    del_uc.execute("dash-1")
    mock_dashboard_repo.delete.assert_called_once_with("dash-1")


def test_list_dashboards_use_case(
    mock_dashboard_repo: MagicMock,
) -> None:
    """Test ListDashboardsUseCase pagination wrapping."""
    dashboard = Dashboard(
        id="dash-1",
        name="Dashboard",
        owner_id="usr-1",
        dataset_id="ds-1",
    )
    mock_dashboard_repo.list.return_value = ([dashboard], 1)

    use_case = ListDashboardsUseCase(mock_dashboard_repo)
    res = use_case.execute(FilterParams(page=1, page_size=20))

    assert res.total == 1
    assert res.page == 1
    assert res.items[0].id == "dash-1"
