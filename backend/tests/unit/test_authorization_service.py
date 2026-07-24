"""Unit tests for AuthorizationService.

Covers permission evaluation, role evaluation, helper methods,
active status enforcement, and edge cases.
"""

from __future__ import annotations

import pytest

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.services.authorization_service import AuthorizationService


@pytest.fixture
def auth_service() -> AuthorizationService:
    """Fixture providing an instance of AuthorizationService."""
    return AuthorizationService()


@pytest.fixture
def read_perm() -> Permission:
    """Fixture providing a read permission."""
    return Permission(
        id="perm-1", resource="dashboard", action="read", description="Read dashboards"
    )


@pytest.fixture
def write_perm() -> Permission:
    """Fixture providing a write permission."""
    return Permission(
        id="perm-2",
        resource="dashboard",
        action="write",
        description="Write dashboards",
    )


@pytest.fixture
def analyst_role(read_perm: Permission) -> Role:
    """Fixture providing an Analyst role with read permission."""
    return Role(
        id="role-1",
        name="analyst",
        description="Analyst Role",
        permissions=[read_perm],
    )


@pytest.fixture
def admin_role(read_perm: Permission, write_perm: Permission) -> Role:
    """Fixture providing an Admin role with read and write permissions."""
    return Role(
        id="role-2",
        name="admin",
        description="Admin Role",
        permissions=[read_perm, write_perm],
    )


@pytest.fixture
def active_user(analyst_role: Role) -> User:
    """Fixture providing an active user with Analyst role."""
    return User(
        id="usr-1",
        email="analyst@nexusbi.io",
        is_active=True,
        roles=[analyst_role],
    )


@pytest.fixture
def active_admin_user(admin_role: Role) -> User:
    """Fixture providing an active admin user with Admin role."""
    return User(
        id="usr-2",
        email="admin@nexusbi.io",
        is_active=True,
        roles=[admin_role],
    )


@pytest.fixture
def inactive_user(analyst_role: Role) -> User:
    """Fixture providing an inactive user with Analyst role."""
    return User(
        id="usr-3",
        email="inactive@nexusbi.io",
        is_active=False,
        roles=[analyst_role],
    )


# ===========================================================================
# Permission Evaluation Tests
# ===========================================================================


class TestPermissionEvaluation:
    """Tests for has_permission, has_any_permission, has_all_permissions,
    and can_access.
    """

    def test_has_permission_success(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """Active user with assigned permission evaluates to True."""
        assert auth_service.has_permission(active_user, "dashboard:read") is True

    def test_has_permission_missing(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """Active user without permission evaluates to False."""
        assert auth_service.has_permission(active_user, "dashboard:write") is False

    def test_has_permission_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """Inactive user evaluates to False even if role possesses the permission."""
        assert auth_service.has_permission(inactive_user, "dashboard:read") is False

    def test_has_any_permission_returns_true_if_at_least_one(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_any_permission returns True when user holds at least one
        requested permission.
        """
        perms = ["dashboard:write", "dashboard:read", "report:delete"]
        assert auth_service.has_any_permission(active_user, perms) is True

    def test_has_any_permission_returns_false_if_none(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_any_permission returns False when user holds none of the permissions."""
        perms = ["dashboard:write", "report:delete"]
        assert auth_service.has_any_permission(active_user, perms) is False

    def test_has_any_permission_empty_list(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_any_permission returns False when permissions sequence is empty."""
        assert auth_service.has_any_permission(active_user, []) is False

    def test_has_any_permission_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """has_any_permission returns False for an inactive user."""
        perms = ["dashboard:read"]
        assert auth_service.has_any_permission(inactive_user, perms) is False

    def test_has_all_permissions_returns_true(
        self, auth_service: AuthorizationService, active_admin_user: User
    ) -> None:
        """has_all_permissions returns True when user holds all requested
        permissions.
        """
        perms = ["dashboard:read", "dashboard:write"]
        assert auth_service.has_all_permissions(active_admin_user, perms) is True

    def test_has_all_permissions_returns_false_if_partially_missing(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_all_permissions returns False when user is missing at least
        one permission.
        """
        perms = ["dashboard:read", "dashboard:write"]
        assert auth_service.has_all_permissions(active_user, perms) is False

    def test_has_all_permissions_empty_list(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_all_permissions returns False when permissions sequence is empty."""
        assert auth_service.has_all_permissions(active_user, []) is False

    def test_has_all_permissions_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """has_all_permissions returns False for an inactive user."""
        perms = ["dashboard:read"]
        assert auth_service.has_all_permissions(inactive_user, perms) is False

    def test_can_access_success(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """can_access returns True for valid resource and action pair."""
        assert auth_service.can_access(active_user, "dashboard", "read") is True

    def test_can_access_denied(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """can_access returns False when permission is missing."""
        assert auth_service.can_access(active_user, "dashboard", "write") is False

    def test_can_access_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """can_access returns False for inactive user."""
        assert auth_service.can_access(inactive_user, "dashboard", "read") is False


# ===========================================================================
# Role Evaluation Tests
# ===========================================================================


class TestRoleEvaluation:
    """Tests for has_role, has_any_role, and has_all_roles."""

    def test_has_role_success(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """Active user with assigned role returns True."""
        assert auth_service.has_role(active_user, "analyst") is True

    def test_has_role_missing(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """Active user without role returns False."""
        assert auth_service.has_role(active_user, "admin") is False

    def test_has_role_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """Inactive user returns False even if role is assigned."""
        assert auth_service.has_role(inactive_user, "analyst") is False

    def test_has_any_role_returns_true(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_any_role returns True when user holds at least one specified role."""
        assert auth_service.has_any_role(active_user, ["admin", "analyst"]) is True

    def test_has_any_role_returns_false(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_any_role returns False when user holds none of the roles."""
        assert auth_service.has_any_role(active_user, ["admin", "superuser"]) is False

    def test_has_any_role_empty_list(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_any_role returns False when role_names sequence is empty."""
        assert auth_service.has_any_role(active_user, []) is False

    def test_has_any_role_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """has_any_role returns False for inactive user."""
        assert auth_service.has_any_role(inactive_user, ["analyst", "admin"]) is False

    def test_has_all_roles_returns_true(
        self,
        auth_service: AuthorizationService,
        analyst_role: Role,
        admin_role: Role,
    ) -> None:
        """has_all_roles returns True when user holds all specified roles."""
        multi_role_user = User(
            id="usr-4",
            email="multi@nexusbi.io",
            is_active=True,
            roles=[analyst_role, admin_role],
        )
        assert auth_service.has_all_roles(multi_role_user, ["analyst", "admin"]) is True

    def test_has_all_roles_returns_false(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_all_roles returns False when user is missing one of the roles."""
        assert auth_service.has_all_roles(active_user, ["analyst", "admin"]) is False

    def test_has_all_roles_empty_list(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """has_all_roles returns False when role_names sequence is empty."""
        assert auth_service.has_all_roles(active_user, []) is False

    def test_has_all_roles_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """has_all_roles returns False for inactive user."""
        assert auth_service.has_all_roles(inactive_user, ["analyst"]) is False


# ===========================================================================
# Helper Methods Tests
# ===========================================================================


class TestHelperMethods:
    """Tests for get_user_permissions and get_user_roles."""

    def test_get_user_permissions_active_user(
        self, auth_service: AuthorizationService, active_admin_user: User
    ) -> None:
        """get_user_permissions returns set of all permission names for active user."""
        perms = auth_service.get_user_permissions(active_admin_user)
        assert perms == {"dashboard:read", "dashboard:write"}

    def test_get_user_permissions_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """get_user_permissions returns empty set for inactive user."""
        assert auth_service.get_user_permissions(inactive_user) == set()

    def test_get_user_roles_active_user(
        self, auth_service: AuthorizationService, active_user: User
    ) -> None:
        """get_user_roles returns set of all role names for active user."""
        roles = auth_service.get_user_roles(active_user)
        assert roles == {"analyst"}

    def test_get_user_roles_inactive_user(
        self, auth_service: AuthorizationService, inactive_user: User
    ) -> None:
        """get_user_roles returns empty set for inactive user."""
        assert auth_service.get_user_roles(inactive_user) == set()


# ===========================================================================
# Edge Case Tests
# ===========================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_user_with_no_roles(self, auth_service: AuthorizationService) -> None:
        """User with empty roles list returns False for all auth checks."""
        no_role_user = User(
            id="usr-5", email="noroles@nexusbi.io", is_active=True, roles=[]
        )
        assert auth_service.has_permission(no_role_user, "dashboard:read") is False
        assert auth_service.has_role(no_role_user, "analyst") is False
        assert auth_service.get_user_permissions(no_role_user) == set()
        assert auth_service.get_user_roles(no_role_user) == set()

    def test_overlapping_permissions_across_roles(
        self,
        auth_service: AuthorizationService,
        read_perm: Permission,
        write_perm: Permission,
    ) -> None:
        """Permissions are deduplicated across multiple roles assigned to a user."""
        r1 = Role(id="r1", name="role1", permissions=[read_perm])
        r2 = Role(id="r2", name="role2", permissions=[read_perm, write_perm])
        user = User(
            id="usr-6",
            email="overlap@nexusbi.io",
            is_active=True,
            roles=[r1, r2],
        )

        perms = auth_service.get_user_permissions(user)
        assert perms == {"dashboard:read", "dashboard:write"}
        assert auth_service.has_permission(user, "dashboard:read") is True
