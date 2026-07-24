"""REST API tests for RBAC dependency integration.

Verifies API authorization behavior using permission dependencies:
- Anonymous access blocked (HTTP 401)
- Authenticated access allowed (HTTP 200)
- Invalid token rejected (HTTP 401)
- Insufficient permissions rejected (HTTP 403)
- Permission dependency execution
  (require_permission, require_any_permission, require_all_permissions)
"""

from __future__ import annotations

from typing import Annotated
from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_current_user,
)
from app.api.dependencies.authorization import (
    require_all_permissions,
    require_any_permission,
    require_permission,
)
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import AuthenticationError, register_exception_handlers
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User

# Router demonstrating future-ready RBAC route protection
rbac_test_router = APIRouter(prefix="/api/v1/test-rbac", tags=["Test RBAC"])


@rbac_test_router.get(
    "/single-perm",
    dependencies=[Depends(require_permission("dashboard:read"))],
)
def single_perm_endpoint(
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    return {"user_id": user.id, "access": "single_perm_granted"}


@rbac_test_router.get(
    "/any-perm",
    dependencies=[Depends(require_any_permission(["dashboard:read", "reports:read"]))],
)
def any_perm_endpoint(
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    return {"user_id": user.id, "access": "any_perm_granted"}


@rbac_test_router.get(
    "/all-perms",
    dependencies=[
        Depends(require_all_permissions(["dashboard:read", "dashboard:write"]))
    ],
)
def all_perms_endpoint(
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    return {"user_id": user.id, "access": "all_perms_granted"}


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI(title="RBAC API Test App")
    register_exception_handlers(app)
    app.include_router(rbac_test_router)
    return app


@pytest.fixture
def rbac_client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def admin_user() -> User:
    read_perm = Permission(id="p1", resource="dashboard", action="read")
    write_perm = Permission(id="p2", resource="dashboard", action="write")
    admin_role = Role(
        id="r1",
        name="Admin",
        description="Admin role",
        permissions=[read_perm, write_perm],
    )
    return User(
        id="usr-admin",
        email="admin@example.com",
        is_active=True,
        roles=[admin_role],
    )


@pytest.fixture
def viewer_user() -> User:
    read_perm = Permission(id="p1", resource="dashboard", action="read")
    viewer_role = Role(
        id="r2",
        name="Viewer",
        description="Viewer role",
        permissions=[read_perm],
    )
    return User(
        id="usr-viewer",
        email="viewer@example.com",
        is_active=True,
        roles=[viewer_role],
    )


class TestRBACApiAccessControl:
    """API integration tests for RBAC dependency enforcement."""

    def test_anonymous_access_blocked(
        self,
        rbac_client: TestClient,
    ) -> None:
        """Anonymous access without authorization header returns HTTP 401."""
        response = rbac_client.get("/api/v1/test-rbac/single-perm")
        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"

    def test_invalid_token_rejected(
        self,
        test_app: FastAPI,
        rbac_client: TestClient,
    ) -> None:
        """Invalid token raises AuthenticationError and returns HTTP 401."""

        def mock_get_current_user_invalid() -> User:
            raise AuthenticationError("Invalid or expired token")

        test_app.dependency_overrides[get_current_user] = mock_get_current_user_invalid

        response = rbac_client.get(
            "/api/v1/test-rbac/single-perm",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"

    def test_authenticated_access_allowed_with_require_permission(
        self,
        test_app: FastAPI,
        rbac_client: TestClient,
        viewer_user: User,
    ) -> None:
        """Authenticated user possessing permission receives HTTP 200."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        test_app.dependency_overrides[get_current_user] = lambda: viewer_user
        test_app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = rbac_client.get(
            "/api/v1/test-rbac/single-perm",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "user_id": viewer_user.id,
            "access": "single_perm_granted",
        }
        mock_auth_svc.has_permission.assert_called_once_with(
            viewer_user, "dashboard:read"
        )

    def test_insufficient_permissions_rejected(
        self,
        test_app: FastAPI,
        rbac_client: TestClient,
        viewer_user: User,
    ) -> None:
        """Authenticated user lacking permission receives HTTP 403 Forbidden."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = False

        test_app.dependency_overrides[get_current_user] = lambda: viewer_user
        test_app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = rbac_client.get(
            "/api/v1/test-rbac/single-perm",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1003"
        mock_auth_svc.has_permission.assert_called_once_with(
            viewer_user, "dashboard:read"
        )

    def test_require_any_permission_execution_allowed(
        self,
        test_app: FastAPI,
        rbac_client: TestClient,
        viewer_user: User,
    ) -> None:
        """require_any_permission allows access if user has one of permissions."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_any_permission.return_value = True

        test_app.dependency_overrides[get_current_user] = lambda: viewer_user
        test_app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = rbac_client.get(
            "/api/v1/test-rbac/any-perm",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "user_id": viewer_user.id,
            "access": "any_perm_granted",
        }
        mock_auth_svc.has_any_permission.assert_called_once_with(
            viewer_user, ["dashboard:read", "reports:read"]
        )

    def test_require_any_permission_insufficient_permissions_rejected(
        self,
        test_app: FastAPI,
        rbac_client: TestClient,
        viewer_user: User,
    ) -> None:
        """require_any_permission returns HTTP 403 if user lacks all permissions."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_any_permission.return_value = False

        test_app.dependency_overrides[get_current_user] = lambda: viewer_user
        test_app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = rbac_client.get(
            "/api/v1/test-rbac/any-perm",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1003"
        mock_auth_svc.has_any_permission.assert_called_once_with(
            viewer_user, ["dashboard:read", "reports:read"]
        )

    def test_require_all_permissions_execution_allowed(
        self,
        test_app: FastAPI,
        rbac_client: TestClient,
        admin_user: User,
    ) -> None:
        """require_all_permissions allows access if user has all permissions."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_all_permissions.return_value = True

        test_app.dependency_overrides[get_current_user] = lambda: admin_user
        test_app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = rbac_client.get(
            "/api/v1/test-rbac/all-perms",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "user_id": admin_user.id,
            "access": "all_perms_granted",
        }
        mock_auth_svc.has_all_permissions.assert_called_once_with(
            admin_user, ["dashboard:read", "dashboard:write"]
        )

    def test_require_all_permissions_insufficient_permissions_rejected(
        self,
        test_app: FastAPI,
        rbac_client: TestClient,
        admin_user: User,
    ) -> None:
        """require_all_permissions returns HTTP 403 if user lacks any permission."""
        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_all_permissions.return_value = False

        test_app.dependency_overrides[get_current_user] = lambda: admin_user
        test_app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        response = rbac_client.get(
            "/api/v1/test-rbac/all-perms",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1003"
        mock_auth_svc.has_all_permissions.assert_called_once_with(
            admin_user, ["dashboard:read", "dashboard:write"]
        )
