"""Unit tests for RBAC Seed Data and Permission Registry.

Covers default roles, default permissions, registry lookups, duplicate detection,
missing permission/role lookups, and default role/permission contents.
"""

from __future__ import annotations

import pytest

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.permission_registry import (
    DEFAULT_PERMISSIONS,
    PermissionRegistry,
    find_permission,
    find_role,
    get_default_permissions,
    get_default_roles,
)


class TestDefaultPermissionsContents:
    """Tests for default permission definitions and helper functions."""

    def test_default_permissions_exist(self) -> None:
        perms = get_default_permissions()
        assert len(perms) > 0
        qnames = {p.qualified_name for p in perms}

        expected_required_permissions = {
            "users:create",
            "users:read",
            "users:update",
            "users:delete",
            "roles:read",
            "roles:update",
            "dashboard:view",
            "dashboard:edit",
            "reports:read",
            "reports:export",
            "settings:update",
        }
        assert expected_required_permissions.issubset(qnames)

    def test_permission_entity_attributes(self) -> None:
        perm = find_permission("users:create")
        assert perm is not None
        assert perm.id == "perm-users-create"
        assert perm.resource == "users"
        assert perm.action == "create"
        assert perm.qualified_name == "users:create"
        assert perm.description is not None
        assert "Create" in perm.description


class TestDefaultRolesContents:
    """Tests for default role definitions and helper functions."""

    def test_all_five_default_roles_exist(self) -> None:
        roles = get_default_roles()
        role_names = {r.name for r in roles}
        expected_roles = {
            "Super Admin",
            "Admin",
            "Manager",
            "Analyst",
            "Viewer",
        }
        assert expected_roles == role_names

    def test_super_admin_role_has_all_permissions(self) -> None:
        super_admin = find_role("Super Admin")
        assert super_admin is not None
        assert len(super_admin.permissions) == len(DEFAULT_PERMISSIONS)
        assert super_admin.has_permission("users:create")
        assert super_admin.has_permission("settings:update")

    def test_admin_role_permissions(self) -> None:
        admin = find_role("Admin")
        assert admin is not None
        assert admin.has_permission("users:create")
        assert admin.has_permission("roles:update")
        assert admin.has_permission("settings:update")

    def test_manager_role_permissions(self) -> None:
        manager = find_role("Manager")
        assert manager is not None
        assert manager.has_permission("users:read")
        assert manager.has_permission("dashboard:view")
        assert manager.has_permission("reports:export")
        assert not manager.has_permission("users:delete")
        assert not manager.has_permission("roles:delete")

    def test_analyst_role_permissions(self) -> None:
        analyst = find_role("Analyst")
        assert analyst is not None
        assert analyst.has_permission("dashboard:view")
        assert analyst.has_permission("dashboard:edit")
        assert analyst.has_permission("reports:export")
        assert not analyst.has_permission("users:create")
        assert not analyst.has_permission("settings:update")

    def test_viewer_role_permissions(self) -> None:
        viewer = find_role("Viewer")
        assert viewer is not None
        assert viewer.has_permission("dashboard:view")
        assert viewer.has_permission("reports:read")
        assert not viewer.has_permission("dashboard:edit")
        assert not viewer.has_permission("reports:export")
        assert not viewer.has_permission("users:read")

    def test_get_default_roles_returns_fresh_instances(self) -> None:
        roles1 = get_default_roles()
        roles2 = get_default_roles()
        assert roles1 is not roles2
        assert roles1[0] is not roles2[0]


class TestRegistryLookups:
    """Tests for PermissionRegistry lookup features."""

    def test_lookup_permission_by_qualified_name(self) -> None:
        perm = find_permission("users:create")
        assert perm is not None
        assert perm.resource == "users"
        assert perm.action == "create"

    def test_lookup_permission_by_resource_and_action(self) -> None:
        perm = find_permission("reports", "export")
        assert perm is not None
        assert perm.qualified_name == "reports:export"

    def test_lookup_permission_by_id(self) -> None:
        registry = PermissionRegistry(permissions=DEFAULT_PERMISSIONS)
        perm = registry.find_permission("perm-settings-update")
        assert perm is not None
        assert perm.qualified_name == "settings:update"

    def test_lookup_role_by_exact_name(self) -> None:
        role = find_role("Super Admin")
        assert role is not None
        assert role.id == "role-super-admin"

    def test_lookup_role_by_normalized_name(self) -> None:
        role1 = find_role("super_admin")
        role2 = find_role("SUPER_ADMIN")
        role3 = find_role("analyst")

        assert role1 is not None
        assert role1.name == "Super Admin"
        assert role2 is not None
        assert role2.name == "Super Admin"
        assert role3 is not None
        assert role3.name == "Analyst"

    def test_lookup_role_by_id(self) -> None:
        role = find_role("role-viewer")
        assert role is not None
        assert role.name == "Viewer"


class TestMissingPermissionsAndRoles:
    """Tests handling of missing permissions and roles."""

    def test_missing_permission_returns_none(self) -> None:
        assert find_permission("nonexistent:permission") is None
        assert find_permission("users", "fly") is None
        assert find_permission("perm-does-not-exist") is None

    def test_missing_role_returns_none(self) -> None:
        assert find_role("NonExistentRole") is None
        assert find_role("unknown-role-id") is None


class TestDuplicateDetection:
    """Tests for duplicate permissions and roles validation."""

    def test_register_duplicate_permission_qualified_name_raises_value_error(
        self,
    ) -> None:
        registry = PermissionRegistry()
        p1 = Permission(id="p1", resource="doc", action="read")
        p2 = Permission(id="p2", resource="doc", action="read")

        registry.register_permission(p1)
        with pytest.raises(ValueError, match="Duplicate permission qualified name"):
            registry.register_permission(p2)

    def test_register_duplicate_permission_id_raises_value_error(
        self,
    ) -> None:
        registry = PermissionRegistry()
        p1 = Permission(id="same-id", resource="doc", action="read")
        p2 = Permission(id="same-id", resource="doc", action="write")

        registry.register_permission(p1)
        with pytest.raises(ValueError, match="Duplicate permission ID"):
            registry.register_permission(p2)

    def test_init_with_duplicate_permissions_raises_value_error(
        self,
    ) -> None:
        p1 = Permission(id="p1", resource="doc", action="read")
        p2 = Permission(id="p2", resource="doc", action="read")

        with pytest.raises(ValueError, match="Duplicate permission qualified name"):
            PermissionRegistry(permissions=[p1, p2])

    def test_register_duplicate_role_name_raises_value_error(self) -> None:
        registry = PermissionRegistry()
        r1 = Role(id="r1", name="CustomRole")
        r2 = Role(id="r2", name="customrole")

        registry.register_role(r1)
        with pytest.raises(ValueError, match="Duplicate role name"):
            registry.register_role(r2)

    def test_register_duplicate_role_id_raises_value_error(self) -> None:
        registry = PermissionRegistry()
        r1 = Role(id="r-same", name="Role One")
        r2 = Role(id="r-same", name="Role Two")

        registry.register_role(r1)
        with pytest.raises(ValueError, match="Duplicate role ID"):
            registry.register_role(r2)
