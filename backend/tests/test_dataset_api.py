"""Comprehensive REST API tests for Dataset Management endpoints.

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
    get_create_dataset_use_case,
    get_current_user,
    get_delete_dataset_use_case,
    get_get_dataset_use_case,
    get_list_datasets_use_case,
    get_update_dataset_use_case,
)
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.dataset_dto import DatasetDTO
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
    """Authenticated user with dataset permissions."""
    perm_create = Permission(
        id="p-ds-c", resource="datasets", action="create", description=""
    )
    perm_read = Permission(
        id="p-ds-r", resource="datasets", action="read", description=""
    )
    perm_update = Permission(
        id="p-ds-u", resource="datasets", action="update", description=""
    )
    perm_delete = Permission(
        id="p-ds-d", resource="datasets", action="delete", description=""
    )
    role = Role(
        id="r-1",
        name="DatasetAdmin",
        permissions=[perm_create, perm_read, perm_update, perm_delete],
    )
    return User(id="usr-ds-001", email="ds-user@nexusbi.io", roles=[role])


@pytest.fixture
def mock_auth_service() -> MagicMock:
    """Mock authorization service that always permits."""
    auth_service = MagicMock(spec=IAuthorizationService)
    auth_service.has_permission.return_value = True
    return auth_service


@pytest.fixture
def sample_dataset_dto() -> DatasetDTO:
    """Sample DatasetDTO for use in test responses."""
    now = datetime.now(UTC)
    return DatasetDTO(
        id="ds-test-1",
        name="Test Dataset",
        source_type="postgres",
        query_or_table="public.test_table",
        owner_id="usr-ds-001",
        description="A test dataset",
        schema_metadata={"columns": ["id", "name"]},
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
# POST /api/v1/datasets
# ---------------------------------------------------------------------------


class TestCreateDatasetEndpoint:
    """Tests for POST /api/v1/datasets."""

    def test_create_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """Successful creation returns HTTP 201 with dataset DTO."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dataset_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_create_dataset_use_case] = lambda: mock_uc

        response = client.post(
            "/api/v1/datasets",
            json={
                "name": "Test Dataset",
                "source_type": "postgres",
                "query_or_table": "public.test_table",
                "description": "A test dataset",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "ds-test-1"
        assert data["name"] == "Test Dataset"
        assert data["source_type"] == "postgres"
        assert data["owner_id"] == "usr-ds-001"
        assert data["is_active"] is True

    def test_create_minimal_payload(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """Minimal required fields succeed."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dataset_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_create_dataset_use_case] = lambda: mock_uc

        response = client.post(
            "/api/v1/datasets",
            json={
                "name": "Minimal",
                "source_type": "csv",
                "query_or_table": "file.csv",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201

    def test_create_validation_error_missing_name(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Missing required 'name' field returns HTTP 422."""
        _setup_auth(app, sample_user, mock_auth_service)

        response = client.post(
            "/api/v1/datasets",
            json={
                "source_type": "postgres",
                "query_or_table": "tbl",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_create_validation_error_empty_name(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Empty string 'name' field returns HTTP 422."""
        _setup_auth(app, sample_user, mock_auth_service)

        response = client.post(
            "/api/v1/datasets",
            json={
                "name": "",
                "source_type": "postgres",
                "query_or_table": "tbl",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/datasets
# ---------------------------------------------------------------------------


class TestListDatasetsEndpoint:
    """Tests for GET /api/v1/datasets."""

    def test_list_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """Listing returns HTTP 200 with paginated response."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[DatasetDTO](
            items=[sample_dataset_dto],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_datasets_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/datasets",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "ds-test-1"

    def test_list_with_filters(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Query parameters are forwarded as filters."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[DatasetDTO](
            items=[], total=0, page=1, page_size=10, total_pages=0
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_datasets_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/datasets?page=2&page_size=10&name=orders"
            "&owner_id=usr-1&is_active=true&sort_by=name&sort_order=asc",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        call_args = mock_uc.execute.call_args[0][0]
        assert call_args.page == 2
        assert call_args.page_size == 10
        assert call_args.name == "orders"
        assert call_args.owner_id == "usr-1"
        assert call_args.is_active is True
        assert call_args.sort_by == "name"
        assert call_args.sort_order == "asc"

    def test_list_with_is_active_false(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """is_active=false filter is correctly parsed."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[DatasetDTO](
            items=[], total=0, page=1, page_size=20, total_pages=0
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_datasets_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/datasets?is_active=false",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        call_args = mock_uc.execute.call_args[0][0]
        assert call_args.is_active is False

    def test_list_empty(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Empty results return valid paginated response."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = PaginatedResponse[DatasetDTO](
            items=[], total=0, page=1, page_size=20, total_pages=0
        )

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_list_datasets_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/datasets",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


# ---------------------------------------------------------------------------
# GET /api/v1/datasets/{dataset_id}
# ---------------------------------------------------------------------------


class TestGetDatasetEndpoint:
    """Tests for GET /api/v1/datasets/{dataset_id}."""

    def test_get_by_id_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """Retrieving an existing dataset returns HTTP 200."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dataset_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_get_dataset_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/datasets/ds-test-1",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "ds-test-1"
        assert data["name"] == "Test Dataset"

    def test_get_by_id_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Requesting a non-existent dataset returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dataset", "missing-id")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_get_dataset_use_case] = lambda: mock_uc

        response = client.get(
            "/api/v1/datasets/missing-id",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/v1/datasets/{dataset_id}
# ---------------------------------------------------------------------------


class TestReplaceDatasetEndpoint:
    """Tests for PUT /api/v1/datasets/{dataset_id}."""

    def test_put_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """PUT request returns HTTP 200 with updated dataset."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dataset_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_dataset_use_case] = lambda: mock_uc

        response = client.put(
            "/api/v1/datasets/ds-test-1",
            json={
                "name": "Updated via PUT",
                "source_type": "snowflake",
                "query_or_table": "analytics.events",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        mock_uc.execute.assert_called_once()

    def test_put_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """PUT on non-existent dataset returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dataset", "missing-id")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_dataset_use_case] = lambda: mock_uc

        response = client.put(
            "/api/v1/datasets/missing-id",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/v1/datasets/{dataset_id}
# ---------------------------------------------------------------------------


class TestUpdateDatasetEndpoint:
    """Tests for PATCH /api/v1/datasets/{dataset_id}."""

    def test_patch_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """PATCH request returns HTTP 200 with updated dataset."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dataset_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_dataset_use_case] = lambda: mock_uc

        response = client.patch(
            "/api/v1/datasets/ds-test-1",
            json={"name": "Patched Dataset"},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "ds-test-1"

    def test_patch_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """PATCH on non-existent dataset returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dataset", "missing-id")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_dataset_use_case] = lambda: mock_uc

        response = client.patch(
            "/api/v1/datasets/missing-id",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404

    def test_patch_partial_update(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
        sample_dataset_dto: DatasetDTO,
    ) -> None:
        """PATCH with single field succeeds."""
        mock_uc = MagicMock()
        mock_uc.execute.return_value = sample_dataset_dto

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_update_dataset_use_case] = lambda: mock_uc

        response = client.patch(
            "/api/v1/datasets/ds-test-1",
            json={"is_active": False},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /api/v1/datasets/{dataset_id}
# ---------------------------------------------------------------------------


class TestDeleteDatasetEndpoint:
    """Tests for DELETE /api/v1/datasets/{dataset_id}."""

    def test_delete_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Successful deletion returns HTTP 204."""
        mock_uc = MagicMock()

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_delete_dataset_use_case] = lambda: mock_uc

        response = client.delete(
            "/api/v1/datasets/ds-test-1",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 204

    def test_delete_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user: User,
        mock_auth_service: MagicMock,
    ) -> None:
        """Deleting a non-existent dataset returns HTTP 404."""
        mock_uc = MagicMock()
        mock_uc.execute.side_effect = EntityNotFoundError("Dataset", "missing-id")

        _setup_auth(app, sample_user, mock_auth_service)
        app.dependency_overrides[get_delete_dataset_use_case] = lambda: mock_uc

        response = client.delete(
            "/api/v1/datasets/missing-id",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404
