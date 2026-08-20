"""Tests for the Protocol-based repository interfaces.

Verifies that:
1. The interfaces are runtime-checkable Protocol classes.
2. Conforming implementations are accepted by isinstance checks.
3. Non-conforming implementations are rejected.
4. All required method signatures are specified.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.session import Session
from app.domain.entities.user import User
from app.domain.repositories.role_repository import IRoleRepository as IRoleRepo
from app.domain.repositories.session_repository import (
    ISessionRepository as ISessionRepo,
)
from app.domain.repositories.user_repository import IUserRepository as IUserRepo

# ── Conforming Stub Implementations ──────────────────────────────────


class _StubUserRepository:
    """Minimal conforming implementation of IUserRepository."""

    def get_by_id(self, _user_id: str) -> User | None:
        return None

    def get_by_email(self, _email: str) -> User | None:
        return None

    def get_by_google_id(self, _google_id: str) -> User | None:
        return None

    def save(self, user: User) -> User:
        return user

    def delete(self, _user_id: str) -> bool:
        return True

    def list_all(self, limit: int = 50, offset: int = 0) -> list[User]:
        return []


class _StubSessionRepository(ISessionRepo):
    """Minimal conforming implementation of ISessionRepository."""

    def get_by_id(self, _session_id: str) -> Session | None:
        return None

    def get_by_token_id(self, _token_id: str) -> Session | None:
        return None

    def get_by_refresh_token(self, _refresh_token: str) -> Session | None:
        return None

    def save(self, session: Session) -> Session:
        return session

    def revoke_by_id(self, _session_id: str) -> bool:
        return True

    def revoke_by_token_id(self, _token_id: str) -> bool:
        return True

    def revoke_all_user_sessions(self, _user_id: str) -> int:
        return 0


# ── Non-conforming Stub ──────────────────────────────────────────────


class _IncompleteUserRepo:
    """Missing required methods — should NOT satisfy the Protocol."""

    def get_by_email(self, _email: str) -> User | None:
        return None


class _IncompleteSessionRepo:
    """Missing required methods — should NOT satisfy the Protocol."""

    def create(self, session: Session) -> Session:
        return session


# ── User Repository Protocol Tests ───────────────────────────────────


class TestIUserRepositoryProtocol:
    """Tests for IUserRepository Protocol contract."""

    def test_conforming_stub_satisfies_protocol(self) -> None:
        repo = _StubUserRepository()
        assert isinstance(repo, IUserRepo)

    def test_non_conforming_stub_does_not_satisfy_protocol(self) -> None:
        repo = _IncompleteUserRepo()
        assert not isinstance(repo, IUserRepo)

    def test_get_by_id_returns_none(self) -> None:
        repo = _StubUserRepository()
        assert repo.get_by_id("u1") is None

    def test_get_by_email_returns_none(self) -> None:
        repo = _StubUserRepository()
        assert repo.get_by_email("test@example.com") is None

    def test_get_by_google_id_returns_none(self) -> None:
        repo = _StubUserRepository()
        assert repo.get_by_google_id("g123") is None

    def test_save_returns_user(self) -> None:
        repo = _StubUserRepository()
        user = User(id="u1", email="test@example.com")
        result = repo.save(user)
        assert result is user

    def test_delete_returns_bool(self) -> None:
        repo = _StubUserRepository()
        assert repo.delete("u1") is True


# ── Session Repository Protocol Tests ────────────────────────────────


class TestISessionRepositoryProtocol:
    """Tests for ISessionRepository Protocol contract."""

    def test_conforming_stub_satisfies_protocol(self) -> None:
        repo = _StubSessionRepository()
        assert isinstance(repo, ISessionRepo)

    def test_non_conforming_stub_does_not_satisfy_protocol(self) -> None:
        repo = _IncompleteSessionRepo()
        assert not isinstance(repo, ISessionRepo)

    def test_create_returns_session(self) -> None:
        repo = _StubSessionRepository()
        session = Session(
            id="s1",
            user_id="u1",
            token_id="tid",
            refresh_token="rt",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        result = repo.save(session)
        assert result is session

    def test_revoke_returns_bool(self) -> None:
        repo = _StubSessionRepository()
        assert repo.revoke_by_id("s1") is True

    def test_get_by_id_returns_none(self) -> None:
        repo = _StubSessionRepository()
        assert repo.get_by_id("s1") is None

    def test_get_by_token_id_returns_none(self) -> None:
        repo = _StubSessionRepository()
        assert repo.get_by_token_id("tid") is None

    def test_get_by_refresh_token_returns_none(self) -> None:
        repo = _StubSessionRepository()
        assert repo.get_by_refresh_token("refresh-token") is None

    def test_revoke_by_token_id_returns_bool(self) -> None:
        repo = _StubSessionRepository()
        assert repo.revoke_by_token_id("tid") is True

    def test_revoke_all_user_sessions_returns_int(self) -> None:
        repo = _StubSessionRepository()
        assert repo.revoke_all_user_sessions("u1") == 0


class _StubRoleRepository(IRoleRepo):
    """Minimal conforming implementation of IRoleRepository."""

    def get_all(self) -> list[Role]:
        return []

    def get_by_id(self, _role_id: str) -> Role | None:
        return None

    def get_by_name(self, _name: str) -> Role | None:
        return None

    def get_permissions_by_ids(self, _permission_ids: list[str]) -> list[Permission]:
        return []

    def save(self, role: Role) -> Role:
        return role

    def delete(self, _role_id: str) -> bool:
        return True


class _IncompleteRoleRepo:
    """Missing required methods — should NOT satisfy Protocol."""

    def get_all(self) -> list[Role]:
        return []


# ── Role Repository Protocol Tests ───────────────────────────────────


class TestIRoleRepositoryProtocol:
    """Tests for IRoleRepository Protocol contract."""

    def test_conforming_stub_satisfies_protocol(self) -> None:
        repo = _StubRoleRepository()
        assert isinstance(repo, IRoleRepo)

    def test_non_conforming_stub_does_not_satisfy_protocol(self) -> None:
        repo = _IncompleteRoleRepo()
        assert not isinstance(repo, IRoleRepo)

    def test_get_all_returns_list(self) -> None:
        repo = _StubRoleRepository()
        assert repo.get_all() == []

    def test_get_by_id_returns_none(self) -> None:
        repo = _StubRoleRepository()
        assert repo.get_by_id("r1") is None

    def test_get_by_name_returns_none(self) -> None:
        repo = _StubRoleRepository()
        assert repo.get_by_name("Admin") is None

    def test_get_permissions_by_ids_returns_list(self) -> None:
        repo = _StubRoleRepository()
        assert repo.get_permissions_by_ids(["p1"]) == []

    def test_save_returns_role(self) -> None:
        repo = _StubRoleRepository()
        role = Role(id="r1", name="Admin")
        assert repo.save(role) is role

    def test_delete_returns_bool(self) -> None:
        repo = _StubRoleRepository()
        assert repo.delete("r1") is True
