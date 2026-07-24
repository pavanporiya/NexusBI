"""Tests for the User domain entity.

Covers construction, invariant validation, lifecycle methods, credential
management, role management, permission queries, and derived properties.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User

# ── Fixtures ──────────────────────────────────────────────────────────


def _perm(resource: str = "dashboard", action: str = "read") -> Permission:
    return Permission(id=f"{resource}_{action}", resource=resource, action=action)


def _role(
    role_id: str = "r1",
    name: str = "analyst",
    perms: list[Permission] | None = None,
) -> Role:
    return Role(id=role_id, name=name, permissions=perms or [])


def _user(
    id: str = "u1",
    email: str = "test@example.com",
    full_name: str | None = None,
    hashed_password: str | None = None,
    is_active: bool = True,
    is_verified: bool = False,
    google_id: str | None = None,
    roles: list[Role] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> User:
    user = User(
        id=id,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        is_active=is_active,
        is_verified=is_verified,
        google_id=google_id,
        roles=roles if roles is not None else [],
    )
    if created_at is not None:
        user.created_at = created_at
    if updated_at is not None:
        user.updated_at = updated_at
    return user


# ── Construction ──────────────────────────────────────────────────────


class TestUserConstruction:
    """Tests for User instantiation and field defaults."""

    def test_basic_construction(self) -> None:
        user = _user()
        assert user.id == "u1"
        assert user.email == "test@example.com"
        assert user.full_name is None
        assert user.hashed_password is None
        assert user.is_active is True
        assert user.is_verified is False
        assert user.google_id is None
        assert user.roles == []
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_construction_with_all_fields(self) -> None:
        now = datetime.now(UTC)
        role = _role()
        user = User(
            id="u2",
            email="full@example.com",
            full_name="Jane Doe",
            hashed_password="hashed_value",
            is_active=False,
            is_verified=True,
            google_id="goog_123",
            roles=[role],
            created_at=now,
            updated_at=now,
        )
        assert user.full_name == "Jane Doe"
        assert user.hashed_password == "hashed_value"
        assert user.is_active is False
        assert user.is_verified is True
        assert user.google_id == "goog_123"
        assert len(user.roles) == 1


class TestUserInvariantValidation:
    """Tests for domain invariant enforcement."""

    def test_empty_email_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="email must not be empty"):
            User(id="u1", email="")

    def test_whitespace_only_email_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="email must not be empty"):
            User(id="u1", email="   ")


# ── Lifecycle Methods ─────────────────────────────────────────────────


class TestUserActivateDeactivate:
    """Tests for activate() and deactivate() methods."""

    def test_deactivate_sets_flag(self) -> None:
        user = _user(is_active=True)
        user.deactivate()
        assert user.is_active is False

    def test_deactivate_is_idempotent(self) -> None:
        user = _user(is_active=False)
        ts_before = user.updated_at
        user.deactivate()
        assert user.is_active is False
        assert user.updated_at == ts_before

    def test_activate_sets_flag(self) -> None:
        user = _user(is_active=False)
        user.activate()
        assert user.is_active is True

    def test_activate_is_idempotent(self) -> None:
        user = _user(is_active=True)
        ts_before = user.updated_at
        user.activate()
        assert user.is_active is True
        assert user.updated_at == ts_before

    def test_deactivate_updates_timestamp(self) -> None:
        user = _user(is_active=True)
        old_ts = user.updated_at
        user.deactivate()
        assert user.updated_at >= old_ts

    def test_activate_updates_timestamp(self) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        user = _user(is_active=False, updated_at=past)
        user.activate()
        assert user.updated_at > past


class TestUserVerifyEmail:
    """Tests for verify_email() method."""

    def test_verify_email_sets_flag(self) -> None:
        user = _user(is_verified=False)
        user.verify_email()
        assert user.is_verified is True

    def test_verify_email_is_idempotent(self) -> None:
        user = _user(is_verified=True)
        ts_before = user.updated_at
        user.verify_email()
        assert user.is_verified is True
        assert user.updated_at == ts_before

    def test_verify_email_updates_timestamp(self) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        user = _user(is_verified=False, updated_at=past)
        user.verify_email()
        assert user.updated_at > past


# ── Credential Management ────────────────────────────────────────────


class TestUserChangePassword:
    """Tests for change_password() method."""

    def test_change_password_updates_hash(self) -> None:
        user = _user(hashed_password="old_hash")
        user.change_password("new_hash")
        assert user.hashed_password == "new_hash"

    def test_change_password_empty_raises_error(self) -> None:
        user = _user()
        with pytest.raises(ValueError, match="Password hash must not be empty"):
            user.change_password("")

    def test_change_password_whitespace_raises_error(self) -> None:
        user = _user()
        with pytest.raises(ValueError, match="Password hash must not be empty"):
            user.change_password("   ")

    def test_change_password_updates_timestamp(self) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        user = _user(updated_at=past)
        user.change_password("new_hash")
        assert user.updated_at > past


# ── Role Management ──────────────────────────────────────────────────


class TestUserAssignRole:
    """Tests for assign_role() method."""

    def test_assign_role_appends(self) -> None:
        user = _user()
        role = _role()
        user.assign_role(role)
        assert len(user.roles) == 1
        assert user.roles[0] is role

    def test_assign_duplicate_role_is_ignored(self) -> None:
        role = _role(role_id="r1")
        user = _user(roles=[role])
        user.assign_role(role)
        assert len(user.roles) == 1

    def test_assign_different_role_succeeds(self) -> None:
        r1 = _role(role_id="r1", name="analyst")
        r2 = _role(role_id="r2", name="admin")
        user = _user(roles=[r1])
        user.assign_role(r2)
        assert len(user.roles) == 2

    def test_assign_role_updates_timestamp(self) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        user = _user(updated_at=past)
        user.assign_role(_role())
        assert user.updated_at > past


class TestUserRemoveRole:
    """Tests for remove_role() method."""

    def test_remove_existing_role(self) -> None:
        role = _role(role_id="r1")
        user = _user(roles=[role])
        user.remove_role("r1")
        assert len(user.roles) == 0

    def test_remove_nonexistent_role_is_safe_noop(self) -> None:
        user = _user(roles=[_role()])
        ts_before = user.updated_at
        user.remove_role("nonexistent")
        assert len(user.roles) == 1
        assert user.updated_at == ts_before

    def test_remove_role_updates_timestamp(self) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        user = _user(roles=[_role()], updated_at=past)
        user.remove_role("r1")
        assert user.updated_at > past


# ── Permission Queries ────────────────────────────────────────────────


class TestUserHasPermission:
    """Tests for has_permission() method."""

    def test_has_permission_through_role(self) -> None:
        perm = _perm("dashboard", "read")
        role = _role(perms=[perm])
        user = _user(roles=[role])
        assert user.has_permission("dashboard:read") is True

    def test_does_not_have_absent_permission(self) -> None:
        role = _role(perms=[_perm("dashboard", "read")])
        user = _user(roles=[role])
        assert user.has_permission("report:write") is False

    def test_has_permission_with_no_roles(self) -> None:
        user = _user()
        assert user.has_permission("dashboard:read") is False

    def test_has_permission_across_multiple_roles(self) -> None:
        r1 = _role(role_id="r1", name="viewer", perms=[_perm("dashboard", "read")])
        r2 = _role(role_id="r2", name="editor", perms=[_perm("report", "write")])
        user = _user(roles=[r1, r2])
        assert user.has_permission("dashboard:read") is True
        assert user.has_permission("report:write") is True


# ── Derived Properties ────────────────────────────────────────────────


class TestUserDerivedProperties:
    """Tests for permission_names and role_names."""

    def test_permission_names_sorted(self) -> None:
        r = _role(
            perms=[
                _perm("report", "write"),
                _perm("dashboard", "read"),
            ]
        )
        user = _user(roles=[r])
        assert user.permission_names == ["dashboard:read", "report:write"]

    def test_permission_names_deduplicated(self) -> None:
        r1 = _role(role_id="r1", name="a", perms=[_perm("dashboard", "read")])
        r2 = _role(role_id="r2", name="b", perms=[_perm("dashboard", "read")])
        user = _user(roles=[r1, r2])
        assert user.permission_names == ["dashboard:read"]

    def test_permission_names_empty_when_no_roles(self) -> None:
        user = _user()
        assert user.permission_names == []

    def test_role_names_returns_all_names(self) -> None:
        r1 = _role(role_id="r1", name="analyst")
        r2 = _role(role_id="r2", name="admin")
        user = _user(roles=[r1, r2])
        assert user.role_names == ["analyst", "admin"]

    def test_role_names_empty_when_no_roles(self) -> None:
        user = _user()
        assert user.role_names == []


class TestUserRepr:
    """Tests for string representation."""

    def test_repr_contains_key_info(self) -> None:
        user = _user()
        r = repr(user)
        assert "User" in r
        assert "test@example.com" in r
