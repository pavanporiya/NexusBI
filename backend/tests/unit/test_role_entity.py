"""Tests for the Role domain entity.

Covers construction, invariant validation, permission management methods,
and backward-compatible ``has_permission`` behavior.
"""

from __future__ import annotations

import pytest

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role

# ── Fixtures ──────────────────────────────────────────────────────────


def _perm(resource: str = "dashboard", action: str = "read") -> Permission:
    """Create a convenience Permission."""
    return Permission(id=f"{resource}_{action}", resource=resource, action=action)


def _role(name: str = "analyst", perms: list[Permission] | None = None) -> Role:
    """Create a convenience Role."""
    return Role(id="r1", name=name, permissions=perms or [])


# ── Construction ──────────────────────────────────────────────────────


class TestRoleConstruction:
    """Tests for Role instantiation and field access."""

    def test_basic_construction(self) -> None:
        role = Role(id="r1", name="admin", description="Full access")
        assert role.id == "r1"
        assert role.name == "admin"
        assert role.description == "Full access"
        assert role.permissions == []

    def test_construction_with_permissions(self) -> None:
        perm = _perm()
        role = Role(id="r1", name="viewer", permissions=[perm])
        assert len(role.permissions) == 1
        assert role.permissions[0] is perm

    def test_default_description_is_none(self) -> None:
        role = Role(id="r1", name="viewer")
        assert role.description is None


class TestRoleInvariantValidation:
    """Tests for domain invariant enforcement."""

    def test_empty_name_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            Role(id="r1", name="")

    def test_whitespace_only_name_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            Role(id="r1", name="   ")


# ── Permission Management ────────────────────────────────────────────


class TestRoleAddPermission:
    """Tests for the add_permission method."""

    def test_add_permission_appends(self) -> None:
        role = _role()
        perm = _perm()
        role.add_permission(perm)
        assert len(role.permissions) == 1
        assert role.permissions[0] is perm

    def test_add_duplicate_permission_is_ignored(self) -> None:
        perm = _perm()
        role = _role(perms=[perm])
        # Same resource:action, different id
        dup = Permission(id="other", resource="dashboard", action="read")
        role.add_permission(dup)
        assert len(role.permissions) == 1

    def test_add_different_permission_succeeds(self) -> None:
        role = _role(perms=[_perm("dashboard", "read")])
        role.add_permission(_perm("dashboard", "write"))
        assert len(role.permissions) == 2


class TestRoleRemovePermission:
    """Tests for the remove_permission method."""

    def test_remove_existing_permission(self) -> None:
        perm = _perm()
        role = _role(perms=[perm])
        role.remove_permission("dashboard:read")
        assert len(role.permissions) == 0

    def test_remove_nonexistent_permission_is_safe_noop(self) -> None:
        role = _role(perms=[_perm()])
        role.remove_permission("nonexistent:action")
        assert len(role.permissions) == 1


class TestRoleContainsPermission:
    """Tests for the contains_permission method."""

    def test_contains_existing_permission(self) -> None:
        role = _role(perms=[_perm()])
        assert role.contains_permission("dashboard:read") is True

    def test_does_not_contain_absent_permission(self) -> None:
        role = _role(perms=[_perm()])
        assert role.contains_permission("dashboard:write") is False


class TestRoleHasPermissionBackwardCompat:
    """Tests for backward-compatible has_permission method."""

    def test_has_permission_with_qualified_name(self) -> None:
        role = _role(perms=[_perm()])
        assert role.has_permission("dashboard:read") is True

    def test_has_permission_returns_false_for_missing(self) -> None:
        role = _role(perms=[_perm()])
        assert role.has_permission("report:write") is False


class TestRoleRepr:
    """Tests for string representation."""

    def test_repr_contains_key_info(self) -> None:
        role = _role(perms=[_perm()])
        r = repr(role)
        assert "Role" in r
        assert "analyst" in r
