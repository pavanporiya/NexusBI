"""Comprehensive REST API tests for Dashboard Management endpoints.

Tests POST, GET, GET by ID, PUT, PATCH, DELETE endpoints with mocked
use cases and authorization, covering success and error scenarios.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_create_dashboard_use_case,
    get_current_user,
    get_delete_dashboard_use_case,
    get_get_dashboard_use_case,
    get_list_dashboards_use_case,
    get_update_dashboard_use_case,
)
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.dashboard_dto import DashboardDTO
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User

# ---------------------------------------------------------------------------
# Shared Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user() -> User:
    """Authenticated user with dashboard permissions."""
    perm_create = Permission(
        id="p-db-c", resource="dashboard", action="create", description=""
    )
    perm_read = Permission(
        id="p-db-r", resource="dashboard", action="read", description=""
    )
    perm_update = Permission(
        id="p-db-u", resource="dashboard", action="update", description=""
    )
    perm_delete = Permission(
        id="p-db-d", resource="dashboard", action="delete", description=""
    )
    role = Role(
        id="r-dash-1",
        name="DashboardAdmin",
        permissions=[perm_create, perm_read, perm_update, perm_delete],
    )
    return User(id="usr-db-001", email="db-user@nexusbi.io", roles=[role])


@pytest.fixture
def mock_auth_service() -> MagicMock:
    """Mock authorization service that permits all requests."""
    auth_service = MagicMock(spec=IAuthorizationService)
    auth_service.has_permission.return_value = True
    return auth_service


@pytest.fixture
def sample_dashboard_dto() -> DashboardDTO:
    """Sample DashboardDTO for test responses."""
    now = datetime.now(UTC)
    return DashboardDTO(
        id="dash-test-1",
        name="Test Executive Dashboard",
        owner_id="usr-db-001",
        dataset_id="ds-test-1",
        description="Core KPIs",
        layout_json={"widgets": [{"id": "w1", "type": "chart"}]},
        is_public=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _setup_auth(
    app: FastAPI,
    user: User,
    auth_service: MagicMock,
) -> None:
    """Wire authentication/authorization dependency overrides."""
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_authorization_service] = lambda: auth_service


# ---------------------------------------------------------------------------
# POST /api/v1/dashboards
# ---------------------------------------------------------------------------


class TestCreateDashboardEndpoint:
    """Tests for POST /api/v1/dashboards."""

    def test_create_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dashboard_dto: DashboardDTO,
    ) -> None:
        """Successful creation returns HTTP 201 with dashboard DTO."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dashboard_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_create_dashboard_use_case] = lambda: mock_uc

        response = client.post(
            "/api/v1/dashboards",
            json={
                "name": "Test Executive Dashboard",
                "dataset_id": "ds-test-1",
                "description": "Core KPIs",
                "layout_json": {"widgets": [{"id": "w1", "type": "chart"}]},
                "is_public": True,
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "dash-test-1"
        assert data["name"] == "Test Executive Dashboard"
        assert data["dataset_id"] == "ds-test-1"
        assert data["owner_id"] == "usr-db-001"
        assert data["is_active"] is True

    def test_create_dataset_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Creating dashboard with non-existent dataset_id returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dataset", "missing-ds")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_create_dashboard_use_case] = lambda: mock_uc

        response = client.post(
            "/api/v1/dashboards",
            json={
                "name": "Invalid Dataset Dashboard",
                "dataset_id": "missing-ds",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404

    def test_create_validation_error_missing_name(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Missing required 'name' returns HTTP 422."""
        _setup_auth(app, sample_user, mock_auth_service)

        response = client.post(
            "/api/v1/dashboards",
            json={"dataset_id": "ds-1"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/dashboards
# ---------------------------------------------------------------------------


class TestListDashboardsEndpoint:
    """Tests for GET /api/v1/dashboards."""

    def test_list_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dashboard_dto: DashboardDTO,
    ) -> None:
        """Listing returns HTTP 200 with paginated response."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[DashboardDTO](
            items=[sample_dashboard_dto],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_dashboards_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/dashboards",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == "dash-test-1"

    def test_list_with_query_filters(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Filters by owner, dataset, active, public, name, sorting."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[DashboardDTO](
            items=[], total=0, page=1, page_size=10, total_pages=0
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_dashboards_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/dashboards?owner=usr-1&dataset=ds-1&active=true&public=true"
            "&name=Sales&sort_by=name&sort_order=asc",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        call_args = mock_uc.execute.call_args[0][0]
        assert call_args.owner_id == "usr-1"
        assert call_args.dataset_id == "ds-1"
        assert call_args.is_active is True
        assert call_args.is_public is True
        assert call_args.name == "Sales"
        assert call_args.sort_by == "name"
        assert call_args.sort_order == "asc"


# ---------------------------------------------------------------------------
# GET /api/v1/dashboards/{dashboard_id}
# ---------------------------------------------------------------------------


class TestGetDashboardEndpoint:
    """Tests for GET /api/v1/dashboards/{dashboard_id}."""

    def test_get_by_id_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dashboard_dto: DashboardDTO,
    ) -> None:
        """Retrieving an existing dashboard returns HTTP 200."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dashboard_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_get_dashboard_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/dashboards/dash-test-1",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "dash-test-1"

    def test_get_by_id_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Requesting a missing dashboard returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dashboard", "missing-id")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_get_dashboard_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/dashboards/missing-id",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/v1/dashboards/{dashboard_id} & PATCH /api/v1/dashboards/{dashboard_id}
# ---------------------------------------------------------------------------


class TestUpdateDashboardEndpoints:
    """Tests for PUT and PATCH /api/v1/dashboards/{dashboard_id}."""

    def test_put_dashboard_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dashboard_dto: DashboardDTO,
    ) -> None:
        """PUT request returns HTTP 200 with updated dashboard."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dashboard_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_dashboard_use_case] = lambda: mock_uc

        response = client.put(
            "/api/v1/dashboards/dash-test-1",
            json={
                "name": "Replaced Title",
                "dataset_id": "ds-test-1",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "dash-test-1"

    def test_patch_dashboard_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dashboard_dto: DashboardDTO,
    ) -> None:
        """PATCH request returns HTTP 200 with updated dashboard."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dashboard_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_dashboard_use_case] = lambda: mock_uc

        response = client.patch(
            "/api/v1/dashboards/dash-test-1",
            json={"is_public": False},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /api/v1/dashboards/{dashboard_id}
# ---------------------------------------------------------------------------


class TestDeleteDashboardEndpoint:
    """Tests for DELETE /api/v1/dashboards/{dashboard_id}."""

    def test_delete_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Deletion returns HTTP 204."""
        mock_uc = MagicMock()

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_delete_dashboard_use_case] = lambda: mock_uc

        response = client.delete(
            "/api/v1/dashboards/dash-test-1",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 204
