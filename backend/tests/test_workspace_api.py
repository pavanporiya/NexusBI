"""REST API tests for Workspace & Membership Management endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_add_member_use_case,
    get_authorization_service,
    get_create_workspace_use_case,
    get_current_user,
    get_delete_workspace_use_case,
    get_get_workspace_use_case,
    get_list_members_use_case,
    get_list_workspaces_use_case,
    get_remove_member_use_case,
    get_update_member_role_use_case,
    get_update_workspace_use_case,
)
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.membership_dto import MembershipDTO
from app.application.dto.workspace_dto import WorkspaceDTO
from app.application.services.interfaces import IAuthorizationService
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User


@pytest.fixture
def sample_ws_user() -> User:
    permissions = [
        Permission(id="p-ws-c", resource="workspaces", action="create", description=""),
        Permission(id="p-ws-r", resource="workspaces", action="read", description=""),
        Permission(id="p-ws-u", resource="workspaces", action="update", description=""),
        Permission(id="p-ws-d", resource="workspaces", action="delete", description=""),
        Permission(id="p-m-c", resource="memberships", action="create", description=""),
        Permission(id="p-m-r", resource="memberships", action="read", description=""),
        Permission(id="p-m-u", resource="memberships", action="update", description=""),
        Permission(id="p-m-d", resource="memberships", action="delete", description=""),
    ]
    role = Role(id="r-ws-admin", name="WSAdmin", permissions=permissions)
    return User(id="usr-ws-001", email="wsadmin@nexusbi.io", roles=[role])


@pytest.fixture
def sample_ws_dto() -> WorkspaceDTO:
    return WorkspaceDTO(
        id="ws-001",
        organization_id="org-001",
        name="Sales Workspace",
        slug="sales-workspace",
        description="Sales analytics workspace",
        is_default=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_mem_dto() -> MembershipDTO:
    return MembershipDTO(
        id="mem-001",
        workspace_id="ws-001",
        user_id="usr-002",
        role_id="role-member",
        joined_at=datetime.now(UTC),
        is_active=True,
    )


def test_create_workspace_api(
    app: FastAPI,
    client: TestClient,
    sample_ws_user: User,
    sample_ws_dto: WorkspaceDTO,
) -> None:
    mock_create_uc = MagicMock()
    mock_create_uc.execute.return_value = sample_ws_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_create_workspace_use_case] = lambda: mock_create_uc

    response = client.post(
        "/api/v1/workspaces",
        json={
            "organization_id": "org-001",
            "name": "Sales Workspace",
            "slug": "sales-workspace",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "ws-001"


def test_get_workspace_api(
    app: FastAPI,
    client: TestClient,
    sample_ws_user: User,
    sample_ws_dto: WorkspaceDTO,
) -> None:
    mock_get_uc = MagicMock()
    mock_get_uc.execute.return_value = sample_ws_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_get_workspace_use_case] = lambda: mock_get_uc

    response = client.get("/api/v1/workspaces/ws-001")
    assert response.status_code == 200
    assert response.json()["id"] == "ws-001"


def test_list_workspaces_api(
    app: FastAPI,
    client: TestClient,
    sample_ws_user: User,
    sample_ws_dto: WorkspaceDTO,
) -> None:
    mock_list_uc = MagicMock()
    mock_list_uc.execute.return_value = PaginatedResponse[WorkspaceDTO](
        items=[sample_ws_dto], total=1, page=1, page_size=20, total_pages=1
    )

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_list_workspaces_use_case] = lambda: mock_list_uc

    response = client.get("/api/v1/workspaces?organization=org-001")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_workspace_api(
    app: FastAPI,
    client: TestClient,
    sample_ws_user: User,
    sample_ws_dto: WorkspaceDTO,
) -> None:
    mock_update_uc = MagicMock()
    mock_update_uc.execute.return_value = sample_ws_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_update_workspace_use_case] = lambda: mock_update_uc

    response = client.patch(
        "/api/v1/workspaces/ws-001",
        json={"name": "Updated Workspace"},
    )
    assert response.status_code == 200


def test_delete_workspace_api(
    app: FastAPI, client: TestClient, sample_ws_user: User
) -> None:
    mock_delete_uc = MagicMock()
    mock_delete_uc.execute.return_value = None

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_delete_workspace_use_case] = lambda: mock_delete_uc

    response = client.delete("/api/v1/workspaces/ws-001")
    assert response.status_code == 204


def test_add_member_api(
    app: FastAPI,
    client: TestClient,
    sample_ws_user: User,
    sample_mem_dto: MembershipDTO,
) -> None:
    mock_add_uc = MagicMock()
    mock_add_uc.execute.return_value = sample_mem_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_add_member_use_case] = lambda: mock_add_uc

    response = client.post(
        "/api/v1/workspaces/ws-001/members",
        json={"user_id": "usr-002", "role_id": "role-member"},
    )
    assert response.status_code == 201
    assert response.json()["user_id"] == "usr-002"


def test_list_members_api(
    app: FastAPI,
    client: TestClient,
    sample_ws_user: User,
    sample_mem_dto: MembershipDTO,
) -> None:
    mock_list_uc = MagicMock()
    mock_list_uc.execute.return_value = PaginatedResponse[MembershipDTO](
        items=[sample_mem_dto], total=1, page=1, page_size=20, total_pages=1
    )

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_list_members_use_case] = lambda: mock_list_uc

    response = client.get("/api/v1/workspaces/ws-001/members")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_member_role_api(
    app: FastAPI,
    client: TestClient,
    sample_ws_user: User,
    sample_mem_dto: MembershipDTO,
) -> None:
    mock_update_role_uc = MagicMock()
    mock_update_role_uc.execute.return_value = sample_mem_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_update_member_role_use_case] = lambda: (
        mock_update_role_uc
    )

    response = client.patch(
        "/api/v1/workspaces/ws-001/members/usr-002",
        json={"role_id": "role-admin"},
    )
    assert response.status_code == 200


def test_remove_member_api(
    app: FastAPI, client: TestClient, sample_ws_user: User
) -> None:
    mock_remove_uc = MagicMock()
    mock_remove_uc.execute.return_value = None

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_ws_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_remove_member_use_case] = lambda: mock_remove_uc

    response = client.delete("/api/v1/workspaces/ws-001/members/usr-002")
    assert response.status_code == 204
