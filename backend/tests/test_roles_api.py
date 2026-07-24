"""REST API tests for Role Management endpoints.

Verifies endpoints:
- GET    /api/v1/roles           → List all RBAC roles
- POST   /api/v1/roles           → Create a new RBAC role
- GET    /api/v1/roles/{role_id} → Retrieve RBAC role details by ID
- PATCH  /api/v1/roles/{role_id} → Update an RBAC role
- DELETE /api/v1/roles/{role_id} → Delete an RBAC role
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_create_role_use_case,
    get_current_user,
    get_delete_role_use_case,
    get_get_role_by_id_use_case,
    get_get_roles_use_case,
    get_update_role_use_case,
)
from app.application.dto.role_dto import PermissionDTO, RoleDTO
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import (
    BusinessRuleViolationError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User


@pytest.fixture
def sample_permission() -> Permission:
    return Permission(
        id="perm-1",
        resource="roles",
        action="read",
        description="Read RBAC roles",
    )


@pytest.fixture
def sample_role_entity(sample_permission: Permission) -> Role:
    return Role(
        id="role-admin",
        name="Admin",
        description="Administrator role",
        permissions=[sample_permission],
    )


@pytest.fixture
def sample_user_entity(sample_role_entity: Role) -> User:
    return User(
        id="usr-123",
        email="testuser@example.com",
        full_name="Test User",
        is_active=True,
        roles=[sample_role_entity],
    )


@pytest.fixture
def sample_role_dto() -> RoleDTO:
    return RoleDTO(
        id="role-admin",
        name="Admin",
        description="Administrator role",
        permissions=[
            PermissionDTO(
                id="perm-1",
                resource="roles",
                action="read",
                description="Read RBAC roles",
            )
        ],
    )


@pytest.fixture
def mock_authorization_service() -> MagicMock:
    auth_service = MagicMock(spec=IAuthorizationService)
    auth_service.has_permission.return_value = True
    return auth_service


@pytest.fixture
def mock_get_roles_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_get_role_by_id_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_create_role_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_update_role_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_delete_role_use_case() -> MagicMock:
    return MagicMock()


class TestGetRolesEndpoint:
    """Tests for GET /api/v1/roles."""

    def test_get_roles_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_get_roles_use_case: MagicMock,
        sample_role_dto: RoleDTO,
    ) -> None:
        """Authorized user receives list of roles with HTTP 200."""
        mock_get_roles_use_case.execute.return_value = [sample_role_dto]
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_get_roles_use_case] = lambda: (
            mock_get_roles_use_case
        )

        response = client.get(
            "/api/v1/roles",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "role-admin"
        assert data[0]["name"] == "Admin"
        assert data[0]["description"] == "Administrator role"
        assert len(data[0]["permissions"]) == 1
        assert data[0]["permissions"][0]["id"] == "perm-1"

    def test_get_roles_empty_list(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_get_roles_use_case: MagicMock,
    ) -> None:
        """Authorized user receives empty list when no roles exist (HTTP 200)."""
        mock_get_roles_use_case.execute.return_value = []
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_get_roles_use_case] = lambda: (
            mock_get_roles_use_case
        )

        response = client.get(
            "/api/v1/roles",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_roles_unauthorized(
        self,
        client: TestClient,
    ) -> None:
        """Unauthenticated request without bearer token returns HTTP 401."""
        response = client.get("/api/v1/roles")
        assert response.status_code == 401

    def test_get_roles_forbidden(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
    ) -> None:
        """Authenticated user lacking roles:read permission returns HTTP 403."""
        mock_authorization_service.has_permission.return_value = False
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )

        response = client.get(
            "/api/v1/roles",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 403


class TestGetRoleByIdEndpoint:
    """Tests for GET /api/v1/roles/{role_id}."""

    def test_get_role_by_id_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_get_role_by_id_use_case: MagicMock,
        sample_role_dto: RoleDTO,
    ) -> None:
        """Authorized user receives role details by ID with HTTP 200."""
        mock_get_role_by_id_use_case.execute.return_value = sample_role_dto
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_get_role_by_id_use_case] = lambda: (
            mock_get_role_by_id_use_case
        )

        response = client.get(
            "/api/v1/roles/role-admin",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "role-admin"
        assert data["name"] == "Admin"
        assert data["description"] == "Administrator role"
        mock_get_role_by_id_use_case.execute.assert_called_once_with("role-admin")

    def test_get_role_by_id_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_get_role_by_id_use_case: MagicMock,
    ) -> None:
        """Request for nonexistent role ID returns HTTP 404 Not Found."""
        mock_get_role_by_id_use_case.execute.side_effect = EntityNotFoundError(
            "Role", "nonexistent-role"
        )
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_get_role_by_id_use_case] = lambda: (
            mock_get_role_by_id_use_case
        )

        response = client.get(
            "/api/v1/roles/nonexistent-role",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-4001"

    def test_get_role_by_id_unauthorized(
        self,
        client: TestClient,
    ) -> None:
        """Unauthenticated request without bearer token returns HTTP 401."""
        response = client.get("/api/v1/roles/role-admin")
        assert response.status_code == 401

    def test_get_role_by_id_forbidden(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
    ) -> None:
        """Authenticated user lacking roles:read permission returns HTTP 403."""
        mock_authorization_service.has_permission.return_value = False
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )

        response = client.get(
            "/api/v1/roles/role-admin",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 403


class TestCreateRoleEndpoint:
    """Tests for POST /api/v1/roles."""

    def test_create_role_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_create_role_use_case: MagicMock,
        sample_role_dto: RoleDTO,
    ) -> None:
        """Authorized user creates a role with HTTP 201 Created."""
        mock_create_role_use_case.execute.return_value = sample_role_dto
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_create_role_use_case] = lambda: (
            mock_create_role_use_case
        )

        response = client.post(
            "/api/v1/roles",
            json={
                "name": "Admin",
                "description": "Administrator role",
                "permission_ids": ["perm-1"],
            },
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "role-admin"
        assert data["name"] == "Admin"

    def test_create_role_duplicate(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_create_role_use_case: MagicMock,
    ) -> None:
        """Duplicate role name returns HTTP 409 Conflict."""
        mock_create_role_use_case.execute.side_effect = DuplicateEntityError(
            "Role", "Admin"
        )
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_create_role_use_case] = lambda: (
            mock_create_role_use_case
        )

        response = client.post(
            "/api/v1/roles",
            json={"name": "Admin"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "NBI-4002"

    def test_create_role_invalid_permission(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_create_role_use_case: MagicMock,
    ) -> None:
        """Nonexistent permission assignment returns HTTP 404 Not Found."""
        mock_create_role_use_case.execute.side_effect = EntityNotFoundError(
            "Permission", "bad-perm"
        )
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_create_role_use_case] = lambda: (
            mock_create_role_use_case
        )

        response = client.post(
            "/api/v1/roles",
            json={"name": "NewRole", "permission_ids": ["bad-perm"]},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NBI-4001"

    def test_create_role_unauthorized(self, client: TestClient) -> None:
        """Unauthenticated request returns HTTP 401."""
        response = client.post("/api/v1/roles", json={"name": "NewRole"})
        assert response.status_code == 401

    def test_create_role_forbidden(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
    ) -> None:
        """Request lacking roles:create permission returns HTTP 403."""
        mock_authorization_service.has_permission.return_value = False
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )

        response = client.post(
            "/api/v1/roles",
            json={"name": "NewRole"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 403


class TestUpdateRoleEndpoint:
    """Tests for PATCH /api/v1/roles/{role_id}."""

    def test_update_role_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_update_role_use_case: MagicMock,
        sample_role_dto: RoleDTO,
    ) -> None:
        """Authorized user updates a role with HTTP 200 OK."""
        mock_update_role_use_case.execute.return_value = sample_role_dto
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_update_role_use_case] = lambda: (
            mock_update_role_use_case
        )

        response = client.patch(
            "/api/v1/roles/role-admin",
            json={"name": "Updated Admin"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "role-admin"

    def test_update_role_duplicate(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_update_role_use_case: MagicMock,
    ) -> None:
        """Updating to existing role name returns HTTP 409 Conflict."""
        mock_update_role_use_case.execute.side_effect = DuplicateEntityError(
            "Role", "ExistingName"
        )
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_update_role_use_case] = lambda: (
            mock_update_role_use_case
        )

        response = client.patch(
            "/api/v1/roles/role-admin",
            json={"name": "ExistingName"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 409

    def test_update_role_invalid_permission(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_update_role_use_case: MagicMock,
    ) -> None:
        """Assigning invalid permission returns HTTP 404 Not Found."""
        mock_update_role_use_case.execute.side_effect = EntityNotFoundError(
            "Permission", "invalid-perm"
        )
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_update_role_use_case] = lambda: (
            mock_update_role_use_case
        )

        response = client.patch(
            "/api/v1/roles/role-admin",
            json={"permission_ids": ["invalid-perm"]},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 404

    def test_update_role_unauthorized(self, client: TestClient) -> None:
        """Unauthenticated request returns HTTP 401."""
        response = client.patch("/api/v1/roles/role-admin", json={"name": "NewName"})
        assert response.status_code == 401

    def test_update_role_forbidden(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
    ) -> None:
        """Request lacking roles:update permission returns HTTP 403."""
        mock_authorization_service.has_permission.return_value = False
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )

        response = client.patch(
            "/api/v1/roles/role-admin",
            json={"name": "NewName"},
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 403


class TestDeleteRoleEndpoint:
    """Tests for DELETE /api/v1/roles/{role_id}."""

    def test_delete_role_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_delete_role_use_case: MagicMock,
    ) -> None:
        """Authorized user deletes a custom role with HTTP 204 No Content."""
        mock_delete_role_use_case.execute.return_value = None
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_delete_role_use_case] = lambda: (
            mock_delete_role_use_case
        )

        response = client.delete(
            "/api/v1/roles/custom-role-1",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 204
        mock_delete_role_use_case.execute.assert_called_once_with("custom-role-1")

    def test_delete_role_protected_default_role(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
        mock_delete_role_use_case: MagicMock,
    ) -> None:
        """Deleting a default system role returns HTTP 422 Business Rule Violation."""
        mock_delete_role_use_case.execute.side_effect = BusinessRuleViolationError(
            rule="Protected default role deletion",
            detail="System default role 'Admin' cannot be deleted.",
        )
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )
        app.dependency_overrides[get_delete_role_use_case] = lambda: (
            mock_delete_role_use_case
        )

        response = client.delete(
            "/api/v1/roles/role-admin",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "NBI-4003"

    def test_delete_role_unauthorized(self, client: TestClient) -> None:
        """Unauthenticated request returns HTTP 401."""
        response = client.delete("/api/v1/roles/custom-role-1")
        assert response.status_code == 401

    def test_delete_role_forbidden(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
        mock_authorization_service: MagicMock,
    ) -> None:
        """Request lacking roles:delete permission returns HTTP 403."""
        mock_authorization_service.has_permission.return_value = False
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity
        app.dependency_overrides[get_authorization_service] = lambda: (
            mock_authorization_service
        )

        response = client.delete(
            "/api/v1/roles/custom-role-1",
            headers={"Authorization": "Bearer valid_access_token"},
        )

        assert response.status_code == 403
