"""Tests for the Protocol-based repository interfaces.

Verifies that:
1. The interfaces are runtime-checkable Protocol classes.
2. Conforming implementations are accepted by isinstance checks.
3. Non-conforming implementations are rejected.
4. All required method signatures are specified.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.entities.role import Role
from app.domain.entities.session import Session
from app.domain.entities.user import User
from app.domain.interfaces.i_session_repository import (
    ISessionRepository as ISessionRepo,
)
from app.domain.interfaces.i_user_repository import IUserRepository as IUserRepo

# ── Conforming Stub Implementations ──────────────────────────────────


class _StubUserRepository:
    """Minimal conforming implementation of IUserRepository."""

    def create(self, user: User) -> User:
        return user

    def update(self, user: User) -> User:
        return user

    def delete(self, _user_id: str) -> bool:
        return True

    def find_by_email(self, _email: str) -> User | None:
        return None

    def find_by_id(self, _user_id: str) -> User | None:
        return None

    def exists(self, _email: str) -> bool:
        return False

    def list_roles(self, _user_id: str) -> list[Role]:
        return []


class _StubSessionRepository:
    """Minimal conforming implementation of ISessionRepository."""

    def create(self, session: Session) -> Session:
        return session

    def revoke(self, _session_id: str) -> bool:
        return True

    def find_active(self, _user_id: str) -> list[Session]:
        return []

    def delete_expired(self) -> int:
        return 0


# ── Non-conforming Stub ──────────────────────────────────────────────


class _IncompleteUserRepo:
    """Missing required methods — should NOT satisfy the Protocol."""

    def find_by_email(self, _email: str) -> User | None:
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

    def test_create_returns_user(self) -> None:
        repo = _StubUserRepository()
        user = User(id="u1", email="test@example.com")
        result = repo.create(user)
        assert result is user

    def test_update_returns_user(self) -> None:
        repo = _StubUserRepository()
        user = User(id="u1", email="test@example.com")
        result = repo.update(user)
        assert result is user

    def test_delete_returns_bool(self) -> None:
        repo = _StubUserRepository()
        assert repo.delete("u1") is True

    def test_find_by_email_returns_none(self) -> None:
        repo = _StubUserRepository()
        assert repo.find_by_email("test@example.com") is None

    def test_find_by_id_returns_none(self) -> None:
        repo = _StubUserRepository()
        assert repo.find_by_id("u1") is None

    def test_exists_returns_bool(self) -> None:
        repo = _StubUserRepository()
        assert repo.exists("test@example.com") is False

    def test_list_roles_returns_empty_list(self) -> None:
        repo = _StubUserRepository()
        assert repo.list_roles("u1") == []


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
        result = repo.create(session)
        assert result is session

    def test_revoke_returns_bool(self) -> None:
        repo = _StubSessionRepository()
        assert repo.revoke("s1") is True

    def test_find_active_returns_empty_list(self) -> None:
        repo = _StubSessionRepository()
        assert repo.find_active("u1") == []

    def test_delete_expired_returns_int(self) -> None:
        repo = _StubSessionRepository()
        assert repo.delete_expired() == 0
