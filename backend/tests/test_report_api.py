"""Comprehensive REST API tests for Report Management endpoints.

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
    get_create_report_use_case,
    get_current_user,
    get_delete_report_use_case,
    get_get_report_use_case,
    get_list_reports_use_case,
    get_update_report_use_case,
)
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.report_dto import ReportDTO
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
    """Authenticated user with report permissions."""
    perm_create = Permission(
        id="p-rep-c", resource="reports", action="create", description=""
    )
    perm_read = Permission(
        id="p-rep-r", resource="reports", action="read", description=""
    )
    perm_update = Permission(
        id="p-rep-u", resource="reports", action="update", description=""
    )
    perm_delete = Permission(
        id="p-rep-d", resource="reports", action="delete", description=""
    )
    role = Role(
        id="r-rep-1",
        name="ReportAdmin",
        permissions=[perm_create, perm_read, perm_update, perm_delete],
    )
    return User(id="usr-rep-001", email="rep-user@nexusbi.io", roles=[role])


@pytest.fixture
def mock_auth_service() -> MagicMock:
    """Mock authorization service that permits all requests."""
    auth_service = MagicMock(spec=IAuthorizationService)
    auth_service.has_permission.return_value = True
    return auth_service


@pytest.fixture
def sample_report_dto() -> ReportDTO:
    """Sample ReportDTO for test responses."""
    now = datetime.now(UTC)
    return ReportDTO(
        id="rep-test-1",
        name="Test Sales Report",
        dataset_id="ds-test-1",
        owner_id="usr-rep-001",
        report_type="tabular",
        output_format="json",
        description="Sales performance metrics",
        schedule="0 0 * * *",
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
# POST /api/v1/reports
# ---------------------------------------------------------------------------


class TestCreateReportEndpoint:
    """Tests for POST /api/v1/reports."""

    def test_create_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_report_dto: ReportDTO,
    ) -> None:
        """Successful creation returns HTTP 201 with report DTO."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_report_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_create_report_use_case] = lambda: mock_uc

        response = client.post(
            "/api/v1/reports",
            json={
                "name": "Test Sales Report",
                "dataset_id": "ds-test-1",
                "report_type": "tabular",
                "output_format": "json",
                "description": "Sales performance metrics",
                "schedule": "0 0 * * *",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "rep-test-1"
        assert data["name"] == "Test Sales Report"
        assert data["dataset_id"] == "ds-test-1"
        assert data["owner_id"] == "usr-rep-001"
        assert data["report_type"] == "tabular"
        assert data["output_format"] == "json"

    def test_create_dataset_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Creating report with non-existent dataset_id returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dataset", "missing-ds")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_create_report_use_case] = lambda: mock_uc

        response = client.post(
            "/api/v1/reports",
            json={
                "name": "Invalid Dataset Report",
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
            "/api/v1/reports",
            json={"dataset_id": "ds-1"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/reports
# ---------------------------------------------------------------------------


class TestListReportsEndpoint:
    """Tests for GET /api/v1/reports."""

    def test_list_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_report_dto: ReportDTO,
    ) -> None:
        """Listing returns HTTP 200 with paginated response."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[ReportDTO](
            items=[sample_report_dto],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_reports_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/reports",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == "rep-test-1"

    def test_list_with_query_filters(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Filters by owner, dataset, report_type, active, name, sorting."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[ReportDTO](
            items=[], total=0, page=1, page_size=10, total_pages=0
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_reports_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/reports?owner=usr-1&dataset=ds-1&report_type=tabular&active=true"
            "&name=Sales&sort_by=name&sort_order=asc",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        call_args = mock_uc.execute.call_args[0][0]
        assert call_args.owner_id == "usr-1"
        assert call_args.dataset_id == "ds-1"
        assert call_args.report_type == "tabular"
        assert call_args.is_active is True
        assert call_args.name == "Sales"
        assert call_args.sort_by == "name"
        assert call_args.sort_order == "asc"


# ---------------------------------------------------------------------------
# GET /api/v1/reports/{report_id}
# ---------------------------------------------------------------------------


class TestGetReportEndpoint:
    """Tests for GET /api/v1/reports/{report_id}."""

    def test_get_by_id_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_report_dto: ReportDTO,
    ) -> None:
        """Retrieving an existing report returns HTTP 200."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_report_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_get_report_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/reports/rep-test-1",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "rep-test-1"

    def test_get_by_id_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Requesting a missing report returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Report", "missing-id")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_get_report_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/reports/missing-id",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT & PATCH /api/v1/reports/{report_id}
# ---------------------------------------------------------------------------


class TestUpdateReportEndpoints:
    """Tests for PUT and PATCH /api/v1/reports/{report_id}."""

    def test_put_report_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_report_dto: ReportDTO,
    ) -> None:
        """PUT request returns HTTP 200 with updated report."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_report_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_report_use_case] = lambda: mock_uc

        response = client.put(
            "/api/v1/reports/rep-test-1",
            json={
                "name": "Replaced Title",
                "dataset_id": "ds-test-1",
                "report_type": "chart",
                "output_format": "pdf",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "rep-test-1"

    def test_patch_report_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_report_dto: ReportDTO,
    ) -> None:
        """PATCH request returns HTTP 200 with updated report."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_report_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_report_use_case] = lambda: mock_uc

        response = client.patch(
            "/api/v1/reports/rep-test-1",
            json={"is_active": False},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /api/v1/reports/{report_id}
# ---------------------------------------------------------------------------


class TestDeleteReportEndpoint:
    """Tests for DELETE /api/v1/reports/{report_id}."""

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
        app.dependency_overrides[get_delete_report_use_case] = lambda: mock_uc

        response = client.delete(
            "/api/v1/reports/rep-test-1",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 204
