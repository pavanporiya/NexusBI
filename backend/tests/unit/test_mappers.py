"""Tests for entity ↔ ORM model mappers.

Verifies that:
1. Domain entities round-trip through mappers without data loss.
2. Email Value Object is properly serialized to/from string.
3. Nested Role/Permission relationships are correctly mapped.
4. Edge cases (None optionals, empty lists) are handled.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.session import Session
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.infrastructure.database.models import (
    PermissionModel,
    RoleModel,
    SessionModel,
    UserModel,
)
from app.infrastructure.mappers.session_mapper import SessionMapper
from app.infrastructure.mappers.user_mapper import UserMapper

# ── Fixtures ─────────────────────────────────────────────────────────

_NOW = datetime.now(UTC)
_LATER = _NOW + timedelta(hours=1)


def _make_permission_model(
    pid: str = "p1",
    resource: str = "dashboard",
    action: str = "read",
) -> PermissionModel:
    return PermissionModel(
        id=pid, resource=resource, action=action, description="Test perm"
    )


def _make_role_model(
    rid: str = "r1",
    name: str = "admin",
    permissions: list[PermissionModel] | None = None,
) -> RoleModel:
    model = RoleModel(id=rid, name=name, description="Test role")
    model.permissions = permissions or []
    return model


def _make_user_model(
    uid: str = "u1",
    roles: list[RoleModel] | None = None,
) -> UserModel:
    model = UserModel(
        id=uid,
        email="test@example.com",
        full_name="Test User",
        hashed_password="$2b$12$hashed",
        is_active=True,
        is_verified=True,
        google_id="g-123",
        created_at=_NOW,
        updated_at=_NOW,
    )
    model.roles = roles or []
    return model


def _make_session_model(sid: str = "s1") -> SessionModel:
    return SessionModel(
        id=sid,
        user_id="u1",
        token_id="jti-abc",
        refresh_token="rt-xyz",
        expires_at=_LATER,
        is_revoked=False,
        revoked_at=None,
        created_at=_NOW,
        updated_at=_NOW,
        client_ip="192.168.1.1",
        user_agent="Mozilla/5.0",
    )


def _make_user_entity(uid: str = "u1") -> User:
    perm = Permission(id="p1", resource="dashboard", action="read")
    role = Role(id="r1", name="admin", description="Admin role", permissions=[perm])
    return User(
        id=uid,
        email="test@example.com",
        full_name="Test User",
        hashed_password="$2b$12$hashed",
        is_active=True,
        is_verified=True,
        google_id="g-123",
        roles=[role],
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_session_entity(sid: str = "s1") -> Session:
    return Session(
        id=sid,
        user_id="u1",
        token_id="jti-abc",
        refresh_token="rt-xyz",
        expires_at=_LATER,
        is_revoked=False,
        revoked_at=None,
        created_at=_NOW,
        updated_at=_NOW,
        client_ip="192.168.1.1",
        user_agent="Mozilla/5.0",
    )


# ── UserMapper Tests ─────────────────────────────────────────────────


class TestUserMapperToDomain:
    """Tests for UserMapper.to_domain()."""

    def test_basic_fields(self) -> None:
        model = _make_user_model()
        entity = UserMapper.to_domain(model)
        assert entity.id == "u1"
        assert entity.full_name == "Test User"
        assert entity.hashed_password == "$2b$12$hashed"
        assert entity.is_active is True
        assert entity.is_verified is True
        assert entity.google_id == "g-123"
        assert entity.created_at == _NOW
        assert entity.updated_at == _NOW

    def test_email_becomes_value_object(self) -> None:
        model = _make_user_model()
        entity = UserMapper.to_domain(model)
        assert isinstance(entity.email, Email)
        assert str(entity.email) == "test@example.com"

    def test_roles_and_permissions_mapped(self) -> None:
        perm_model = _make_permission_model()
        role_model = _make_role_model(permissions=[perm_model])
        model = _make_user_model(roles=[role_model])

        entity = UserMapper.to_domain(model)
        assert len(entity.roles) == 1
        assert entity.roles[0].name == "admin"
        assert len(entity.roles[0].permissions) == 1
        assert entity.roles[0].permissions[0].resource == "dashboard"
        assert entity.roles[0].permissions[0].action == "read"

    def test_empty_roles(self) -> None:
        model = _make_user_model(roles=[])
        entity = UserMapper.to_domain(model)
        assert entity.roles == []

    def test_none_optional_fields(self) -> None:
        model = UserModel(
            id="u2",
            email="bare@example.com",
            full_name=None,
            hashed_password=None,
            is_active=True,
            is_verified=False,
            google_id=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
        model.roles = []
        entity = UserMapper.to_domain(model)
        assert entity.full_name is None
        assert entity.hashed_password is None
        assert entity.google_id is None


class TestUserMapperToModel:
    """Tests for UserMapper.to_model()."""

    def test_basic_fields(self) -> None:
        entity = _make_user_entity()
        model = UserMapper.to_model(entity)
        assert model.id == "u1"
        assert model.email == "test@example.com"
        assert model.full_name == "Test User"
        assert model.hashed_password == "$2b$12$hashed"
        assert model.is_active is True
        assert model.is_verified is True
        assert model.google_id == "g-123"

    def test_email_serialized_to_string(self) -> None:
        entity = _make_user_entity()
        model = UserMapper.to_model(entity)
        assert isinstance(model.email, str)
        assert model.email == "test@example.com"

    def test_timestamps_preserved(self) -> None:
        entity = _make_user_entity()
        model = UserMapper.to_model(entity)
        assert model.created_at == _NOW
        assert model.updated_at == _NOW


class TestUserMapperUpdateModel:
    """Tests for UserMapper.update_model()."""

    def test_updates_mutable_fields(self) -> None:
        model = _make_user_model()
        entity = _make_user_entity()
        entity.full_name = "Updated Name"

        result = UserMapper.update_model(model, entity)
        assert result is model  # same instance
        assert model.full_name == "Updated Name"

    def test_updates_email(self) -> None:
        model = _make_user_model()
        entity = User(
            id="u1",
            email="new@example.com",
            is_active=True,
            created_at=_NOW,
            updated_at=_NOW,
        )

        UserMapper.update_model(model, entity)
        assert model.email == "new@example.com"


# ── SessionMapper Tests ──────────────────────────────────────────────


class TestSessionMapperToDomain:
    """Tests for SessionMapper.to_domain()."""

    def test_basic_fields(self) -> None:
        model = _make_session_model()
        entity = SessionMapper.to_domain(model)
        assert entity.id == "s1"
        assert entity.user_id == "u1"
        assert entity.token_id == "jti-abc"
        assert entity.refresh_token == "rt-xyz"
        assert entity.expires_at == _LATER
        assert entity.is_revoked is False
        assert entity.revoked_at is None
        assert entity.client_ip == "192.168.1.1"
        assert entity.user_agent == "Mozilla/5.0"

    def test_timestamps(self) -> None:
        model = _make_session_model()
        entity = SessionMapper.to_domain(model)
        assert entity.created_at == _NOW
        assert entity.updated_at == _NOW

    def test_none_optional_fields(self) -> None:
        model = SessionModel(
            id="s2",
            user_id="u1",
            token_id="jti-def",
            refresh_token="rt-abc",
            expires_at=_LATER,
            is_revoked=False,
            revoked_at=None,
            created_at=_NOW,
            updated_at=_NOW,
            client_ip=None,
            user_agent=None,
        )
        entity = SessionMapper.to_domain(model)
        assert entity.client_ip is None
        assert entity.user_agent is None


class TestSessionMapperToModel:
    """Tests for SessionMapper.to_model()."""

    def test_basic_fields(self) -> None:
        entity = _make_session_entity()
        model = SessionMapper.to_model(entity)
        assert model.id == "s1"
        assert model.user_id == "u1"
        assert model.token_id == "jti-abc"
        assert model.refresh_token == "rt-xyz"

    def test_timestamps_preserved(self) -> None:
        entity = _make_session_entity()
        model = SessionMapper.to_model(entity)
        assert model.created_at == _NOW
        assert model.updated_at == _NOW


class TestSessionMapperUpdateModel:
    """Tests for SessionMapper.update_model()."""

    def test_updates_mutable_fields(self) -> None:
        model = _make_session_model()
        entity = _make_session_entity()
        entity.is_revoked = True
        new_time = _NOW + timedelta(minutes=30)
        entity.revoked_at = new_time
        entity.updated_at = new_time

        result = SessionMapper.update_model(model, entity)
        assert result is model
        assert model.is_revoked is True
        assert model.revoked_at == new_time
        assert model.updated_at == new_time

    def test_updates_token_fields(self) -> None:
        model = _make_session_model()
        entity = _make_session_entity()
        entity.token_id = "new-jti"
        entity.refresh_token = "new-rt"

        SessionMapper.update_model(model, entity)
        assert model.token_id == "new-jti"
        assert model.refresh_token == "new-rt"
