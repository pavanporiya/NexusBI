"""Unit tests for FastAPI authorization dependencies.

Covers require_permission, require_any_permission, require_all_permissions,
auth dependencies, error conditions, and FastAPI dependency orchestration.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_current_user,
)
from app.api.dependencies.authorization import (
    AllPermissionsDependency,
    AnyPermissionDependency,
    PermissionDependency,
    require_all_permissions,
    require_any_permission,
    require_permission,
)
from app.application.dto.auth_dto import UserDTO
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User


@pytest.fixture
def active_user() -> User:
    """Fixture providing an active user entity with standard permissions."""
    read_perm = Permission(id="p1", resource="dashboard", action="read")
    write_perm = Permission(id="p2", resource="dashboard", action="write")
    analyst_role = Role(
        id="r1",
        name="analyst",
        description="Analyst role",
        permissions=[read_perm, write_perm],
    )
    return User(
        id="usr-100",
        email="analyst@example.com",
        is_active=True,
        roles=[analyst_role],
    )


@pytest.fixture
def auth_service() -> MagicMock:
    """Fixture providing a mocked IAuthorizationService."""
    return MagicMock(spec=IAuthorizationService)


class TestRequirePermission:
    """Tests for require_permission dependency factory."""

    def test_factory_returns_permission_dependency(self) -> None:
        """Factory returns a PermissionDependency instance."""
        dep = require_permission("dashboard:read")
        assert isinstance(dep, PermissionDependency)
        assert dep.permission == "dashboard:read"

    def test_permission_granted_returns_user(
        self, active_user: User, auth_service: MagicMock
    ) -> None:
        """Authorized user is returned when permission check passes."""
        auth_service.has_permission.return_value = True
        dep = require_permission("dashboard:read")

        result = dep(current_user=active_user, auth_service=auth_service)

        assert result == active_user
        auth_service.has_permission.assert_called_once_with(
            active_user, "dashboard:read"
        )

    def test_permission_denied_raises_authorization_error(
        self, active_user: User, auth_service: MagicMock
    ) -> None:
        """AuthorizationError (HTTP 403) is raised when permission check fails."""
        auth_service.has_permission.return_value = False
        dep = require_permission("dashboard:delete")

        with pytest.raises(AuthorizationError) as exc_info:
            dep(current_user=active_user, auth_service=auth_service)

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "NBI-1003"
        assert "dashboard:delete" in str(exc_info.value.detail)


class TestRequireAnyPermission:
    """Tests for require_any_permission dependency factory."""

    def test_factory_returns_any_permission_dependency(self) -> None:
        """Factory returns an AnyPermissionDependency instance."""
        perms = ["dashboard:read", "report:view"]
        dep = require_any_permission(perms)
        assert isinstance(dep, AnyPermissionDependency)
        assert dep.permissions == perms

    def test_any_permission_granted_returns_user(
        self, active_user: User, auth_service: MagicMock
    ) -> None:
        """Authorized user is returned when user has at least one permission."""
        auth_service.has_any_permission.return_value = True
        perms = ["dashboard:read", "report:delete"]
        dep = require_any_permission(perms)

        result = dep(current_user=active_user, auth_service=auth_service)

        assert result == active_user
        auth_service.has_any_permission.assert_called_once_with(active_user, perms)

    def test_any_permission_denied_raises_authorization_error(
        self, active_user: User, auth_service: MagicMock
    ) -> None:
        """AuthorizationError is raised when user possesses none of permissions."""
        auth_service.has_any_permission.return_value = False
        perms = ["admin:delete", "system:configure"]
        dep = require_any_permission(perms)

        with pytest.raises(AuthorizationError) as exc_info:
            dep(current_user=active_user, auth_service=auth_service)

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "NBI-1003"


class TestRequireAllPermissions:
    """Tests for require_all_permissions dependency factory."""

    def test_factory_returns_all_permissions_dependency(self) -> None:
        """Factory returns an AllPermissionsDependency instance."""
        perms = ["dashboard:read", "dashboard:write"]
        dep = require_all_permissions(perms)
        assert isinstance(dep, AllPermissionsDependency)
        assert dep.permissions == perms

    def test_all_permissions_granted_returns_user(
        self, active_user: User, auth_service: MagicMock
    ) -> None:
        """Authorized user is returned when user possesses all permissions."""
        auth_service.has_all_permissions.return_value = True
        perms = ["dashboard:read", "dashboard:write"]
        dep = require_all_permissions(perms)

        result = dep(current_user=active_user, auth_service=auth_service)

        assert result == active_user
        auth_service.has_all_permissions.assert_called_once_with(active_user, perms)

    def test_all_permissions_denied_raises_authorization_error(
        self, active_user: User, auth_service: MagicMock
    ) -> None:
        """AuthorizationError is raised when user lacks at least one permission."""
        auth_service.has_all_permissions.return_value = False
        perms = ["dashboard:read", "admin:delete"]
        dep = require_all_permissions(perms)

        with pytest.raises(AuthorizationError) as exc_info:
            dep(current_user=active_user, auth_service=auth_service)

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "NBI-1003"


class TestAuthDependencies:
    """Tests for auth resolution dependency providers."""

    def test_get_authorization_service_returns_instance(self) -> None:
        """get_authorization_service returns a valid IAuthorizationService."""
        svc = get_authorization_service()
        assert isinstance(svc, IAuthorizationService)

    def test_get_current_user_success(self, active_user: User) -> None:
        """get_current_user resolves token via use case and loads user entity."""
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        use_case = MagicMock()
        user_repo = MagicMock()

        user_dto = UserDTO(
            id=active_user.id,
            email=str(active_user.email),
            is_active=True,
            roles=["analyst"],
            permissions=["dashboard:read"],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        use_case.execute.return_value = user_dto
        user_repo.get_by_id.return_value = active_user

        user = get_current_user(
            credentials=creds, use_case=use_case, user_repo=user_repo
        )

        assert user == active_user
        use_case.execute.assert_called_once_with("valid-token")
        user_repo.get_by_id.assert_called_once_with(active_user.id)

    def test_get_current_user_missing_credentials(self) -> None:
        """get_current_user raises AuthenticationError when credentials missing."""
        use_case = MagicMock()
        user_repo = MagicMock()

        with pytest.raises(AuthenticationError) as exc_info:
            get_current_user(credentials=None, use_case=use_case, user_repo=user_repo)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.message

    def test_get_current_user_inactive_user(self, active_user: User) -> None:
        """get_current_user raises AuthenticationError if user is inactive."""
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        use_case = MagicMock()
        user_repo = MagicMock()

        user_dto = UserDTO(
            id=active_user.id,
            email=str(active_user.email),
            is_active=True,
            roles=[],
            permissions=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        use_case.execute.return_value = user_dto

        active_user.is_active = False
        user_repo.get_by_id.return_value = active_user

        with pytest.raises(AuthenticationError) as exc_info:
            get_current_user(credentials=creds, use_case=use_case, user_repo=user_repo)

        assert exc_info.value.status_code == 401


class TestFastAPIIntegration:
    """Integration tests executing dependencies within FastAPI routes."""

    def test_fastapi_route_with_require_permission_success(
        self, active_user: User
    ) -> None:
        """FastAPI route returns 200 when require_permission passes."""
        app = FastAPI()

        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = True

        app.dependency_overrides[get_current_user] = lambda: active_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        metrics_permission = require_permission("metrics:read")

        @app.get("/metrics")
        def metrics_endpoint(
            user: User = Depends(metrics_permission),
        ) -> dict[str, str]:
            return {"user_id": user.id, "status": "allowed"}

        client = TestClient(app)
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.json() == {"user_id": active_user.id, "status": "allowed"}

    def test_fastapi_route_with_require_permission_forbidden(
        self, active_user: User
    ) -> None:
        """FastAPI route returns 403 when require_permission fails."""
        from app.core.exceptions import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)

        mock_auth_svc = MagicMock(spec=IAuthorizationService)
        mock_auth_svc.has_permission.return_value = False

        app.dependency_overrides[get_current_user] = lambda: active_user
        app.dependency_overrides[get_authorization_service] = lambda: mock_auth_svc

        admin_permission = require_permission("admin:manage")

        @app.get("/admin")
        def admin_endpoint(
            user: User = Depends(admin_permission),
        ) -> dict[str, str]:
            _ = user
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/admin")

        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1003"
