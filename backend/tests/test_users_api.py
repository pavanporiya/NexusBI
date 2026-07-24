"""REST API tests for User Management endpoints.

Verifies User Management endpoints:
- GET   /api/v1/users/me        → Current authenticated user profile
- GET   /api/v1/users/{user_id} → User profile retrieval by ID
- PATCH /api/v1/users/{user_id} → User profile details update
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_current_user,
    get_get_user_use_case,
    get_update_user_use_case,
)
from app.application.dto.auth_dto import UserDTO
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.user import User


@pytest.fixture
def sample_user_entity() -> User:
    now = datetime.now(UTC)
    return User(
        id="usr-123",
        email="testuser@example.com",
        full_name="Test User",
        is_active=True,
        roles=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_user_dto() -> UserDTO:
    now = datetime.now(UTC)
    return UserDTO(
        id="usr-123",
        email="testuser@example.com",
        full_name="Test User",
        is_active=True,
        roles=["User"],
        permissions=["users:read"],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_get_user_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_update_user_use_case() -> MagicMock:
    return MagicMock()


class TestGetCurrentUserEndpoint:
    """Tests for GET /api/v1/users/me."""

    def test_get_me_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
    ) -> None:
        """Authenticated user receives profile with HTTP 200."""
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "usr-123"
        assert data["email"] == "testuser@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True

    def test_get_me_unauthenticated(
        self,
        client: TestClient,
    ) -> None:
        """Missing authorization header returns HTTP 401."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"


class TestGetUserByIdEndpoint:
    """Tests for GET /api/v1/users/{user_id}."""

    def test_get_user_by_id_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        sample_user_dto: UserDTO,
        mock_get_user_use_case: MagicMock,
    ) -> None:
        """Authorized request returns user details with HTTP 200."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        mock_get_user_use_case.execute.return_value = sample_user_dto

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
        app.dependency_overrides[get_get_user_use_case] = lambda: mock_get_user_use_case

        response = client.get(
            "/api/v1/users/usr-123",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "usr-123"
        assert data["email"] == "testuser@example.com"
        mock_auth_svc.has_permission.assert_called_once_with(
            sample_user_entity, "users:read"
        )
        mock_get_user_use_case.execute.assert_called_once_with("usr-123")

    def test_get_user_by_id_unauthenticated(
        self,
        client: TestClient,
    ) -> None:
        """Unauthenticated access returns HTTP 401."""
        response = client.get("/api/v1/users/usr-123")

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"

    def test_get_user_by_id_permission_denied(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
    ) -> None:
        """User lacking users:read permission returns HTTP 403."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = False

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = client.get(
            "/api/v1/users/usr-123",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1003"
        mock_auth_svc.has_permission.assert_called_once_with(
            sample_user_entity, "users:read"
        )

    def test_get_user_by_id_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_get_user_use_case: MagicMock,
    ) -> None:
        """Request for non-existent user returns HTTP 404."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        mock_get_user_use_case.execute.side_effect = EntityNotFoundError(
            "User", "usr-missing"
        )

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
        app.dependency_overrides[get_get_user_use_case] = lambda: mock_get_user_use_case

        response = client.get(
            "/api/v1/users/usr-missing",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-4001"


class TestUpdateUserEndpoint:
    """Tests for PATCH /api/v1/users/{user_id}."""

    def test_update_user_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_update_user_use_case: MagicMock,
    ) -> None:
        """Authorized user with update permission receives HTTP 200."""
        now = datetime.now(UTC)
        updated_dto = UserDTO(
            id="usr-123",
            email="testuser@example.com",
            full_name="New Name",
            is_active=True,
            roles=["User"],
            permissions=["users:update"],
            created_at=now,
            updated_at=now,
        )

        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        mock_update_user_use_case.execute.return_value = updated_dto

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
        app.dependency_overrides[get_update_user_use_case] = lambda: (
            mock_update_user_use_case
        )

        response = client.patch(
            "/api/v1/users/usr-123",
            json={"full_name": "New Name"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "usr-123"
        assert data["full_name"] == "New Name"
        mock_auth_svc.has_permission.assert_called_once_with(
            sample_user_entity, "users:update"
        )
        mock_update_user_use_case.execute.assert_called_once()

    def test_update_user_unauthenticated(
        self,
        client: TestClient,
    ) -> None:
        """Unauthenticated update attempt returns HTTP 401."""
        response = client.patch(
            "/api/v1/users/usr-123",
            json={"full_name": "New Name"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"

    def test_update_user_permission_denied(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
    ) -> None:
        """User lacking users:update permission returns HTTP 403."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = False

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = client.patch(
            "/api/v1/users/usr-123",
            json={"full_name": "New Name"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1003"
        mock_auth_svc.has_permission.assert_called_once_with(
            sample_user_entity, "users:update"
        )

    def test_update_user_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_update_user_use_case: MagicMock,
    ) -> None:
        """Attempting to update a non-existent user returns HTTP 404."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        mock_update_user_use_case.execute.side_effect = EntityNotFoundError(
            "User", "usr-missing"
        )

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
        app.dependency_overrides[get_update_user_use_case] = lambda: (
            mock_update_user_use_case
        )

        response = client.patch(
            "/api/v1/users/usr-missing",
            json={"full_name": "New Name"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-4001"

    def test_update_user_validation_error(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
    ) -> None:
        """Sending invalid email format returns HTTP 422 validation error."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = client.patch(
            "/api/v1/users/usr-123",
            json={"email": "invalid-email-format"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1001"

    def test_update_user_duplicate_email(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_update_user_use_case: MagicMock,
    ) -> None:
        """Updating to an email already in use returns HTTP 409 Conflict."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        mock_update_user_use_case.execute.side_effect = DuplicateEntityError(
            "User", "taken@example.com"
        )

        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
        app.dependency_overrides[get_update_user_use_case] = lambda: (
            mock_update_user_use_case
        )

        response = client.patch(
            "/api/v1/users/usr-123",
            json={"email": "taken@example.com"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-4002"
