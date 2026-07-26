"""REST API tests for Organization Management endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_create_organization_use_case,
    get_current_user,
    get_delete_organization_use_case,
    get_get_organization_use_case,
    get_list_organizations_use_case,
    get_update_organization_use_case,
)
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.organization_dto import OrganizationDTO
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User


@pytest.fixture
def sample_org_user() -> User:
    perm_create = Permission(
        id="p-org-c", resource="organizations", action="create", description=""
    )
    perm_read = Permission(
        id="p-org-r", resource="organizations", action="read", description=""
    )
    perm_update = Permission(
        id="p-org-u", resource="organizations", action="update", description=""
    )
    perm_delete = Permission(
        id="p-org-d", resource="organizations", action="delete", description=""
    )
    role = Role(
        id="r-org-admin",
        name="OrgAdmin",
        permissions=[perm_create, perm_read, perm_update, perm_delete],
    )
    return User(id="usr-org-001", email="orgadmin@nexusbi.io", roles=[role])


@pytest.fixture
def sample_org_dto() -> OrganizationDTO:
    return OrganizationDTO(
        id="org-001",
        name="Acme Inc",
        slug="acme-inc",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_create_organization_api(
    app: FastAPI,
    client: TestClient,
    sample_org_user: User,
    sample_org_dto: OrganizationDTO,
) -> None:
    mock_create_uc = MagicMock()
    mock_create_uc.execute.return_value = sample_org_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_org_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_create_organization_use_case] = lambda: mock_create_uc

    response = client.post(
        "/api/v1/organizations",
        json={"name": "Acme Inc", "slug": "acme-inc"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "org-001"
    assert data["name"] == "Acme Inc"


def test_get_organization_api(
    app: FastAPI,
    client: TestClient,
    sample_org_user: User,
    sample_org_dto: OrganizationDTO,
) -> None:
    mock_get_uc = MagicMock()
    mock_get_uc.execute.return_value = sample_org_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_org_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_get_organization_use_case] = lambda: mock_get_uc

    response = client.get("/api/v1/organizations/org-001")
    assert response.status_code == 200
    assert response.json()["id"] == "org-001"


def test_get_organization_not_found_api(
    app: FastAPI, client: TestClient, sample_org_user: User
) -> None:
    mock_get_uc = MagicMock()
    mock_get_uc.execute.side_effect = EntityNotFoundError("Organization", "org-999")

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_org_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_get_organization_use_case] = lambda: mock_get_uc

    response = client.get("/api/v1/organizations/org-999")
    assert response.status_code == 404


def test_list_organizations_api(
    app: FastAPI,
    client: TestClient,
    sample_org_user: User,
    sample_org_dto: OrganizationDTO,
) -> None:
    mock_list_uc = MagicMock()
    mock_list_uc.execute.return_value = PaginatedResponse[OrganizationDTO](
        items=[sample_org_dto], total=1, page=1, page_size=20, total_pages=1
    )

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_org_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_list_organizations_use_case] = lambda: mock_list_uc

    response = client.get("/api/v1/organizations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "org-001"


def test_update_organization_api(
    app: FastAPI,
    client: TestClient,
    sample_org_user: User,
    sample_org_dto: OrganizationDTO,
) -> None:
    mock_update_uc = MagicMock()
    mock_update_uc.execute.return_value = sample_org_dto

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_org_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_update_organization_use_case] = lambda: mock_update_uc

    response = client.patch(
        "/api/v1/organizations/org-001",
        json={"name": "Acme Inc Updated"},
    )
    assert response.status_code == 200


def test_delete_organization_api(
    app: FastAPI, client: TestClient, sample_org_user: User
) -> None:
    mock_delete_uc = MagicMock()
    mock_delete_uc.execute.return_value = None

    mock_auth_svc = MagicMock(spec=IAuthorizationService)
    mock_auth_svc.has_permission.return_value = True

    app.dependency_overrides[get_current_user] = lambda: sample_org_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc
    app.dependency_overrides[get_delete_organization_use_case] = lambda: mock_delete_uc

    response = client.delete("/api/v1/organizations/org-001")
    assert response.status_code == 204
