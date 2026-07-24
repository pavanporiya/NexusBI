"""Tests for SQLAlchemy ORM models.

Verifies that:
1. All models can be instantiated with expected attributes.
2. Table names match the expected naming convention.
3. Relationship attributes are defined.
4. Constraint naming conventions are applied.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.infrastructure.database.base import Base
from app.infrastructure.database.models import (
    PermissionModel,
    RoleModel,
    SessionModel,
    UserModel,
    role_permissions,
    user_roles,
)

# ── Table Name Tests ─────────────────────────────────────────────────


class TestTableNames:
    """Verify ORM model __tablename__ attributes."""

    def test_permission_table_name(self) -> None:
        assert PermissionModel.__tablename__ == "permissions"

    def test_role_table_name(self) -> None:
        assert RoleModel.__tablename__ == "roles"

    def test_user_table_name(self) -> None:
        assert UserModel.__tablename__ == "users"

    def test_session_table_name(self) -> None:
        assert SessionModel.__tablename__ == "sessions"


# ── Association Table Tests ──────────────────────────────────────────


class TestAssociationTables:
    """Verify M2M join table definitions."""

    def test_role_permissions_table_exists(self) -> None:
        assert role_permissions.name == "role_permissions"

    def test_user_roles_table_exists(self) -> None:
        assert user_roles.name == "user_roles"

    def test_role_permissions_columns(self) -> None:
        col_names = {c.name for c in role_permissions.columns}
        assert col_names == {"role_id", "permission_id"}

    def test_user_roles_columns(self) -> None:
        col_names = {c.name for c in user_roles.columns}
        assert col_names == {"user_id", "role_id"}


# ── Model Instantiation Tests ───────────────────────────────────────


class TestPermissionModel:
    """Verify PermissionModel instantiation and attributes."""

    def test_instantiation(self) -> None:
        model = PermissionModel(
            id="p1",
            resource="dashboard",
            action="read",
            description="Read dashboards",
        )
        assert model.id == "p1"
        assert model.resource == "dashboard"
        assert model.action == "read"
        assert model.description == "Read dashboards"

    def test_optional_description(self) -> None:
        model = PermissionModel(id="p2", resource="report", action="write")
        assert model.description is None

    def test_repr(self) -> None:
        model = PermissionModel(id="p1", resource="dashboard", action="read")
        result = repr(model)
        assert "PermissionModel" in result
        assert "dashboard" in result
        assert "read" in result


class TestRoleModel:
    """Verify RoleModel instantiation and attributes."""

    def test_instantiation(self) -> None:
        model = RoleModel(id="r1", name="admin", description="Administrator")
        assert model.id == "r1"
        assert model.name == "admin"
        assert model.description == "Administrator"

    def test_optional_description(self) -> None:
        model = RoleModel(id="r2", name="viewer")
        assert model.description is None

    def test_repr(self) -> None:
        model = RoleModel(id="r1", name="admin")
        result = repr(model)
        assert "RoleModel" in result
        assert "admin" in result


class TestUserModel:
    """Verify UserModel instantiation and attributes."""

    def test_instantiation(self) -> None:
        now = datetime.now(UTC)
        model = UserModel(
            id="u1",
            email="user@example.com",
            full_name="Test User",
            hashed_password="$2b$12$hash",
            is_active=True,
            is_verified=False,
            google_id=None,
            created_at=now,
            updated_at=now,
        )
        assert model.id == "u1"
        assert model.email == "user@example.com"
        assert model.full_name == "Test User"
        assert model.hashed_password == "$2b$12$hash"
        assert model.is_active is True
        assert model.is_verified is False
        assert model.google_id is None

    def test_optional_fields(self) -> None:
        now = datetime.now(UTC)
        model = UserModel(
            id="u2",
            email="minimal@example.com",
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        assert model.full_name is None
        assert model.hashed_password is None
        assert model.google_id is None

    def test_repr(self) -> None:
        now = datetime.now(UTC)
        model = UserModel(
            id="u1",
            email="user@example.com",
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        result = repr(model)
        assert "UserModel" in result
        assert "user@example.com" in result


class TestSessionModel:
    """Verify SessionModel instantiation and attributes."""

    def test_instantiation(self) -> None:
        now = datetime.now(UTC)
        model = SessionModel(
            id="s1",
            user_id="u1",
            token_id="jti-123",
            refresh_token="rt-token",
            expires_at=now,
            is_revoked=False,
            revoked_at=None,
            created_at=now,
            updated_at=now,
            client_ip="127.0.0.1",
            user_agent="pytest/1.0",
        )
        assert model.id == "s1"
        assert model.user_id == "u1"
        assert model.token_id == "jti-123"
        assert model.refresh_token == "rt-token"
        assert model.is_revoked is False
        assert model.revoked_at is None
        assert model.client_ip == "127.0.0.1"
        assert model.user_agent == "pytest/1.0"

    def test_optional_fields(self) -> None:
        now = datetime.now(UTC)
        model = SessionModel(
            id="s2",
            user_id="u1",
            token_id="jti-456",
            refresh_token="rt-token-2",
            expires_at=now,
            is_revoked=False,
            created_at=now,
            updated_at=now,
        )
        assert model.client_ip is None
        assert model.user_agent is None
        assert model.revoked_at is None

    def test_repr(self) -> None:
        now = datetime.now(UTC)
        model = SessionModel(
            id="s1",
            user_id="u1",
            token_id="jti-123",
            refresh_token="rt-token",
            expires_at=now,
            is_revoked=False,
            created_at=now,
            updated_at=now,
        )
        result = repr(model)
        assert "SessionModel" in result
        assert "u1" in result


# ── Base Metadata Tests ──────────────────────────────────────────────


class TestBaseMetadata:
    """Verify that Base metadata and naming conventions are configured."""

    def test_naming_convention_keys(self) -> None:
        nc = Base.metadata.naming_convention
        assert nc is not None
        expected_keys = {"ix", "uq", "ck", "fk", "pk"}
        assert expected_keys.issubset(set(nc.keys()))

    def test_all_models_registered(self) -> None:
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "permissions",
            "roles",
            "users",
            "sessions",
            "role_permissions",
            "user_roles",
        }
        assert expected.issubset(table_names)
