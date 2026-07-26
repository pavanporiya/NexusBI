"""REST API tests for BI Foundation endpoints (Dashboards, Reports, Datasets)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_create_dashboard_use_case,
    get_create_dataset_use_case,
    get_create_report_use_case,
    get_current_user,
    get_delete_dashboard_use_case,
    get_delete_dataset_use_case,
    get_get_dashboard_use_case,
    get_get_report_use_case,
    get_list_dashboards_use_case,
    get_update_dataset_use_case,
)
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.dashboard_dto import DashboardDTO
from app.application.dto.dataset_dto import DatasetDTO
from app.application.dto.report_dto import ReportDTO
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User


@pytest.fixture
def sample_user() -> User:
    perm = Permission(
        id="p-1", resource="dashboard", action="create", description="desc"
    )
    role = Role(id="r-1", name="Admin", permissions=[perm])
    return User(id="usr-123", email="user@nexusbi.io", roles=[role])


@pytest.fixture
def mock_auth_service() -> MagicMock:
    auth_service = MagicMock(spec=IAuthorizationService)
    auth_service.has_permission.return_value = True
    return auth_service


@pytest.fixture
def sample_dashboard_dto() -> DashboardDTO:
    now = datetime.now(UTC)
    return DashboardDTO(
        id="dash-1",
        name="Executive Dashboard",
        owner_id="usr-123",
        dataset_id="ds-1",
        description="Key metrics",
        layout_json={"widgets": []},
        is_public=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_report_dto() -> ReportDTO:
    now = datetime.now(UTC)
    return ReportDTO(
        id="rep-1",
        name="Monthly Sales Report",
        dataset_id="ds-1",
        owner_id="usr-123",
        report_type="tabular",
        output_format="json",
        description="Sales overview",
        schedule="0 0 * * *",
        is_active=True,
        query="SELECT * FROM sales",
        visualization_type="table",
        config={},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_dataset_dto() -> DatasetDTO:
    now = datetime.now(UTC)
    return DatasetDTO(
        id="ds-1",
        name="Orders Dataset",
        source_type="postgres",
        query_or_table="public.orders",
        owner_id="usr-123",
        description="Orders table",
        schema_metadata={},
        is_active=True,
        created_at=now,
        updated_at=now,
    )


class TestDashboardAPI:
    """Tests for /api/v1/dashboards REST endpoints."""

    def test_create_dashboard_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dashboard_dto: DashboardDTO,
    ) -> None:
        """Create dashboard endpoint returns HTTP 201."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dashboard_dto

        app.dependency_overrides[get_current_user] = lambda: sample_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
        app.dependency_overrides[get_create_dashboard_use_case] = lambda: mock_uc

        response = client.post(
            "/api/v1/dashboards",
            json={
                "name": "Executive Dashboard",
                "dataset_id": "ds-1",
                "description": "Key metrics",
            },
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "dash-1"
        assert data["name"] == "Executive Dashboard"

    def test_list_dashboards_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dashboard_dto: DashboardDTO,
    ) -> None:
        """List dashboards endpoint returns HTTP 200 with pagination."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[DashboardDTO](
            items=[sample_dashboard_dto],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )

        app.dependency_overrides[get_current_user] = lambda: sample_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
        app.dependency_overrides[get_list_dashboards_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/dashboards?page=1&page_size=20&search=Executive",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == "dash-1"

    def test_get_dashboard_by_id_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Get missing dashboard returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dashboard", "missing-id")

        app.dependency_overrides[get_current_user] = lambda: sample_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
        app.dependency_overrides[get_get_dashboard_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/dashboards/missing-id",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 404

    def test_delete_dashboard_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Delete dashboard returns HTTP 204."""
        mock_uc = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: sample_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
        app.dependency_overrides[get_delete_dashboard_use_case] = lambda: mock_uc

        response = client.delete(
            "/api/v1/dashboards/dash-1",
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 204


class TestReportAPI:
    """Tests for /api/v1/reports REST endpoints."""

    def test_create_and_get_report(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_report_dto: ReportDTO,
    ) -> None:
        """Test creating and retrieving report."""
        mock_create = MagicMock()
        mock_create.execute.return_value = sample_report_dto
        mock_get = MagicMock()
        mock_get.execute.return_value = sample_report_dto

        app.dependency_overrides[get_current_user] = lambda: sample_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
        app.dependency_overrides[get_create_report_use_case] = lambda: mock_create
        app.dependency_overrides[get_get_report_use_case] = lambda: mock_get

        post_resp = client.post(
            "/api/v1/reports",
            json={
                "name": "Monthly Sales Report",
                "dataset_id": "ds-1",
                "query": "SELECT * FROM sales",
            },
            headers={"Authorization": "Bearer token"},
        )
        assert post_resp.status_code == 201

        get_resp = client.get(
            "/api/v1/reports/rep-1",
            headers={"Authorization": "Bearer token"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == "rep-1"


class TestDatasetAPI:
    """Tests for /api/v1/datasets REST endpoints."""

    def test_dataset_crud_flow(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """Test dataset CRUD API endpoints."""
        mock_create = MagicMock()
        mock_create.execute.return_value = sample_dataset_dto
        mock_update = MagicMock()
        mock_update.execute.return_value = sample_dataset_dto
        mock_delete = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: sample_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
        app.dependency_overrides[get_create_dataset_use_case] = lambda: mock_create
        app.dependency_overrides[get_update_dataset_use_case] = lambda: mock_update
        app.dependency_overrides[get_delete_dataset_use_case] = lambda: mock_delete

        # Create
        res1 = client.post(
            "/api/v1/datasets",
            json={
                "name": "Orders Dataset",
                "source_type": "postgres",
                "query_or_table": "public.orders",
            },
            headers={"Authorization": "Bearer token"},
        )
        assert res1.status_code == 201

        # Patch
        res2 = client.patch(
            "/api/v1/datasets/ds-1",
            json={"name": "Updated Dataset"},
            headers={"Authorization": "Bearer token"},
        )
        assert res2.status_code == 200

        # Delete
        res3 = client.delete(
            "/api/v1/datasets/ds-1",
            headers={"Authorization": "Bearer token"},
        )
        assert res3.status_code == 204
