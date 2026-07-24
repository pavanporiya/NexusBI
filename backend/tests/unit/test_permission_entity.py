"""Tests for the Permission domain entity.

Covers construction, immutability, equality, hashing, and derived properties.
"""

from __future__ import annotations

import pytest

from app.domain.entities.permission import Permission


class TestPermissionConstruction:
    """Tests for Permission instantiation and field access."""

    def test_basic_construction(self) -> None:
        perm = Permission(
            id="p1", resource="dashboard", action="read", description="View dashboards"
        )
        assert perm.id == "p1"
        assert perm.resource == "dashboard"
        assert perm.action == "read"
        assert perm.description == "View dashboards"

    def test_default_description_is_none(self) -> None:
        perm = Permission(id="p2", resource="report", action="write")
        assert perm.description is None


class TestPermissionQualifiedName:
    """Tests for the qualified_name property."""

    def test_qualified_name_format(self) -> None:
        perm = Permission(id="p1", resource="dashboard", action="read")
        assert perm.qualified_name == "dashboard:read"

    def test_name_alias_returns_qualified_name(self) -> None:
        perm = Permission(id="p1", resource="dashboard", action="write")
        assert perm.name == "dashboard:write"
        assert perm.name == perm.qualified_name


class TestPermissionImmutability:
    """Tests that Permission is frozen (immutable)."""

    def test_cannot_modify_id(self) -> None:
        perm = Permission(id="p1", resource="dashboard", action="read")
        with pytest.raises(AttributeError):
            perm.id = "p2"  # type: ignore[misc]

    def test_cannot_modify_resource(self) -> None:
        perm = Permission(id="p1", resource="dashboard", action="read")
        with pytest.raises(AttributeError):
            perm.resource = "report"  # type: ignore[misc]

    def test_cannot_modify_action(self) -> None:
        perm = Permission(id="p1", resource="dashboard", action="read")
        with pytest.raises(AttributeError):
            perm.action = "write"  # type: ignore[misc]


class TestPermissionEquality:
    """Tests for value-based equality on resource:action."""

    def test_same_resource_action_are_equal(self) -> None:
        p1 = Permission(id="p1", resource="dashboard", action="read")
        p2 = Permission(id="p2", resource="dashboard", action="read")
        assert p1 == p2

    def test_different_resource_are_not_equal(self) -> None:
        p1 = Permission(id="p1", resource="dashboard", action="read")
        p2 = Permission(id="p1", resource="report", action="read")
        assert p1 != p2

    def test_different_action_are_not_equal(self) -> None:
        p1 = Permission(id="p1", resource="dashboard", action="read")
        p2 = Permission(id="p1", resource="dashboard", action="write")
        assert p1 != p2

    def test_not_equal_to_non_permission(self) -> None:
        perm = Permission(id="p1", resource="dashboard", action="read")
        assert perm != "dashboard:read"


class TestPermissionHashing:
    """Tests for hash consistency with equality."""

    def test_equal_permissions_have_same_hash(self) -> None:
        p1 = Permission(id="p1", resource="dashboard", action="read")
        p2 = Permission(id="p2", resource="dashboard", action="read")
        assert hash(p1) == hash(p2)

    def test_can_be_used_in_set(self) -> None:
        p1 = Permission(id="p1", resource="dashboard", action="read")
        p2 = Permission(id="p2", resource="dashboard", action="read")
        p3 = Permission(id="p3", resource="dashboard", action="write")
        perm_set = {p1, p2, p3}
        assert len(perm_set) == 2


class TestPermissionRepr:
    """Tests for string representation."""

    def test_repr_contains_fields(self) -> None:
        perm = Permission(id="p1", resource="dashboard", action="read")
        r = repr(perm)
        assert "Permission" in r
        assert "dashboard" in r
        assert "read" in r
