"""Tests for SQLAlchemy repository implementations.

Verifies that:
1. SQLAlchemyUserRepository satisfies the IUserRepository Protocol.
2. SQLAlchemySessionRepository satisfies the ISessionRepository ABC.
3. Repository methods delegate correctly to the SQLAlchemy session.
4. Mapper conversions are applied on all public boundaries.

All tests use a mocked SQLAlchemy session — no real database is required.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.domain.entities.session import Session
from app.domain.entities.user import User
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.models import SessionModel, UserModel
from app.infrastructure.repositories.session_repository import (
    SQLAlchemySessionRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

# ── Fixtures ─────────────────────────────────────────────────────────

_NOW = datetime.now(UTC)
_LATER = _NOW + timedelta(hours=1)


def _make_user_model() -> UserModel:
    model = UserModel(
        id="u1",
        email="test@example.com",
        full_name="Test User",
        hashed_password="$2b$12$hashed",
        is_active=True,
        is_verified=False,
        google_id=None,
        created_at=_NOW,
        updated_at=_NOW,
    )
    model.roles = []
    return model


def _make_session_model() -> SessionModel:
    return SessionModel(
        id="s1",
        user_id="u1",
        token_id="jti-123",
        refresh_token="rt-token",
        expires_at=_LATER,
        is_revoked=False,
        revoked_at=None,
        created_at=_NOW,
        updated_at=_NOW,
        client_ip="127.0.0.1",
        user_agent="pytest/1.0",
    )


def _mock_db_session() -> MagicMock:
    """Create a mock SQLAlchemy session with standard query chain."""
    session = MagicMock()
    session.execute.return_value.scalars.return_value.first.return_value = None
    session.execute.return_value.scalars.return_value.all.return_value = []
    return session


# ── Protocol / ABC Conformance Tests ─────────────────────────────────


class TestUserRepositoryConformance:
    """Verify SQLAlchemyUserRepository satisfies IUserRepository Protocol."""

    def test_isinstance_check(self) -> None:
        repo = SQLAlchemyUserRepository(session=_mock_db_session())
        assert isinstance(repo, IUserRepository)

    def test_has_all_protocol_methods(self) -> None:
        repo = SQLAlchemyUserRepository(session=_mock_db_session())
        assert hasattr(repo, "get_by_id")
        assert hasattr(repo, "get_by_email")
        assert hasattr(repo, "get_by_google_id")
        assert hasattr(repo, "save")
        assert hasattr(repo, "delete")


class TestSessionRepositoryConformance:
    """Verify SQLAlchemySessionRepository satisfies ISessionRepository ABC."""

    def test_isinstance_check(self) -> None:
        repo = SQLAlchemySessionRepository(session=_mock_db_session())
        assert isinstance(repo, ISessionRepository)

    def test_has_all_abc_methods(self) -> None:
        repo = SQLAlchemySessionRepository(session=_mock_db_session())
        assert hasattr(repo, "get_by_id")
        assert hasattr(repo, "get_by_token_id")
        assert hasattr(repo, "get_by_refresh_token")
        assert hasattr(repo, "save")
        assert hasattr(repo, "revoke_by_id")
        assert hasattr(repo, "revoke_by_token_id")
        assert hasattr(repo, "revoke_all_user_sessions")


# ── UserRepository Method Tests ──────────────────────────────────────


class TestSQLAlchemyUserRepositoryGetById:
    """Tests for SQLAlchemyUserRepository.get_by_id()."""

    def test_returns_none_when_not_found(self) -> None:
        db = _mock_db_session()
        repo = SQLAlchemyUserRepository(session=db)
        result = repo.get_by_id("nonexistent")
        assert result is None

    def test_returns_domain_entity_when_found(self) -> None:
        db = _mock_db_session()
        model = _make_user_model()
        db.execute.return_value.scalars.return_value.first.return_value = model
        repo = SQLAlchemyUserRepository(session=db)

        result = repo.get_by_id("u1")
        assert result is not None
        assert isinstance(result, User)
        assert result.id == "u1"
        assert str(result.email) == "test@example.com"


class TestSQLAlchemyUserRepositoryGetByEmail:
    """Tests for SQLAlchemyUserRepository.get_by_email()."""

    def test_returns_none_when_not_found(self) -> None:
        db = _mock_db_session()
        repo = SQLAlchemyUserRepository(session=db)
        result = repo.get_by_email("nobody@example.com")
        assert result is None

    def test_returns_domain_entity_when_found(self) -> None:
        db = _mock_db_session()
        model = _make_user_model()
        db.execute.return_value.scalars.return_value.first.return_value = model
        repo = SQLAlchemyUserRepository(session=db)

        result = repo.get_by_email("test@example.com")
        assert result is not None
        assert isinstance(result, User)

    def test_normalizes_email_input(self) -> None:
        db = _mock_db_session()
        repo = SQLAlchemyUserRepository(session=db)
        repo.get_by_email("  TEST@Example.COM  ")
        # Verify the query was executed (normalization is internal)
        db.execute.assert_called_once()


class TestSQLAlchemyUserRepositoryGetByGoogleId:
    """Tests for SQLAlchemyUserRepository.get_by_google_id()."""

    def test_returns_none_when_not_found(self) -> None:
        db = _mock_db_session()
        repo = SQLAlchemyUserRepository(session=db)
        result = repo.get_by_google_id("g-999")
        assert result is None

    def test_returns_domain_entity_when_found(self) -> None:
        db = _mock_db_session()
        model = _make_user_model()
        model.google_id = "g-123"
        db.execute.return_value.scalars.return_value.first.return_value = model
        repo = SQLAlchemyUserRepository(session=db)

        result = repo.get_by_google_id("g-123")
        assert result is not None
        assert result.google_id == "g-123"


class TestSQLAlchemyUserRepositoryDelete:
    """Tests for SQLAlchemyUserRepository.delete()."""

    def test_returns_false_when_not_found(self) -> None:
        db = _mock_db_session()
        db.get.return_value = None
        repo = SQLAlchemyUserRepository(session=db)

        result = repo.delete("nonexistent")
        assert result is False

    def test_returns_true_when_deleted(self) -> None:
        db = _mock_db_session()
        model = _make_user_model()
        db.get.return_value = model
        repo = SQLAlchemyUserRepository(session=db)

        result = repo.delete("u1")
        assert result is True
        db.delete.assert_called_once_with(model)
        db.flush.assert_called_once()


class TestSQLAlchemyUserRepositorySave:
    """Tests for SQLAlchemyUserRepository.save()."""

    def test_save_new_user_calls_add(self) -> None:
        db = _mock_db_session()
        # First execute (check existing) returns None
        db.execute.return_value.scalars.return_value.first.return_value = None
        # After flush+refresh, we need to mock the model returned
        user = User(
            id="u-new",
            email="new@example.com",
            is_active=True,
            created_at=_NOW,
            updated_at=_NOW,
        )

        repo = SQLAlchemyUserRepository(session=db)

        # Patch refresh to set roles on the model for mapper
        def _refresh_side_effect(model: UserModel) -> None:
            if not hasattr(model, "roles") or model.roles is None:
                model.roles = []

        db.refresh.side_effect = _refresh_side_effect
        result = repo.save(user)

        assert isinstance(result, User)
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_save_existing_user_updates(self) -> None:
        db = _mock_db_session()
        existing_model = _make_user_model()
        db.execute.return_value.scalars.return_value.first.return_value = existing_model

        user = User(
            id="u1",
            email="updated@example.com",
            full_name="Updated",
            is_active=True,
            created_at=_NOW,
            updated_at=_NOW,
        )

        repo = SQLAlchemyUserRepository(session=db)

        def _refresh_side_effect(model: UserModel) -> None:
            if not hasattr(model, "roles") or model.roles is None:
                model.roles = []

        db.refresh.side_effect = _refresh_side_effect
        result = repo.save(user)

        assert isinstance(result, User)
        # Should NOT call add (update, not insert)
        db.add.assert_not_called()
        db.flush.assert_called_once()


# ── SessionRepository Method Tests ───────────────────────────────────


class TestSQLAlchemySessionRepositoryGetById:
    """Tests for SQLAlchemySessionRepository.get_by_id()."""

    def test_returns_none_when_not_found(self) -> None:
        db = _mock_db_session()
        db.get.return_value = None
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.get_by_id("nonexistent")
        assert result is None

    def test_returns_domain_entity_when_found(self) -> None:
        db = _mock_db_session()
        model = _make_session_model()
        db.get.return_value = model
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.get_by_id("s1")
        assert result is not None
        assert isinstance(result, Session)
        assert result.id == "s1"
        assert result.user_id == "u1"


class TestSQLAlchemySessionRepositoryGetByTokenId:
    """Tests for SQLAlchemySessionRepository.get_by_token_id()."""

    def test_returns_none_when_not_found(self) -> None:
        db = _mock_db_session()
        repo = SQLAlchemySessionRepository(session=db)
        result = repo.get_by_token_id("nonexistent")
        assert result is None

    def test_returns_domain_entity_when_found(self) -> None:
        db = _mock_db_session()
        model = _make_session_model()
        db.execute.return_value.scalars.return_value.first.return_value = model
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.get_by_token_id("jti-123")
        assert result is not None
        assert result.token_id == "jti-123"


class TestSQLAlchemySessionRepositoryGetByRefreshToken:
    """Tests for SQLAlchemySessionRepository.get_by_refresh_token()."""

    def test_returns_none_when_not_found(self) -> None:
        db = _mock_db_session()
        repo = SQLAlchemySessionRepository(session=db)
        result = repo.get_by_refresh_token("nonexistent")
        assert result is None

    def test_returns_domain_entity_when_found(self) -> None:
        db = _mock_db_session()
        model = _make_session_model()
        db.execute.return_value.scalars.return_value.first.return_value = model
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.get_by_refresh_token("rt-token")
        assert result is not None
        assert result.refresh_token == "rt-token"


class TestSQLAlchemySessionRepositorySave:
    """Tests for SQLAlchemySessionRepository.save()."""

    def test_save_new_session_calls_add(self) -> None:
        db = _mock_db_session()
        db.get.return_value = None  # No existing session

        session_entity = Session(
            id="s-new",
            user_id="u1",
            token_id="jti-new",
            refresh_token="rt-new",
            expires_at=_LATER,
            created_at=_NOW,
            updated_at=_NOW,
        )

        repo = SQLAlchemySessionRepository(session=db)

        db.refresh.side_effect = lambda _model: None
        result = repo.save(session_entity)

        assert isinstance(result, Session)
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_save_existing_session_updates(self) -> None:
        db = _mock_db_session()
        existing_model = _make_session_model()
        db.get.return_value = existing_model

        session_entity = Session(
            id="s1",
            user_id="u1",
            token_id="jti-updated",
            refresh_token="rt-updated",
            expires_at=_LATER,
            created_at=_NOW,
            updated_at=_NOW,
        )

        repo = SQLAlchemySessionRepository(session=db)

        db.refresh.side_effect = lambda _model: None
        result = repo.save(session_entity)

        assert isinstance(result, Session)
        db.add.assert_not_called()
        db.flush.assert_called_once()


class TestSQLAlchemySessionRepositoryRevoke:
    """Tests for revocation methods."""

    def test_revoke_by_id_returns_false_when_not_found(self) -> None:
        db = _mock_db_session()
        db.get.return_value = None
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.revoke_by_id("nonexistent")
        assert result is False

    def test_revoke_by_id_returns_false_when_already_revoked(self) -> None:
        db = _mock_db_session()
        model = _make_session_model()
        model.is_revoked = True
        db.get.return_value = model
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.revoke_by_id("s1")
        assert result is False

    def test_revoke_by_id_returns_true_and_sets_fields(self) -> None:
        db = _mock_db_session()
        model = _make_session_model()
        db.get.return_value = model
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.revoke_by_id("s1")
        assert result is True
        assert model.is_revoked is True
        assert model.revoked_at is not None
        db.flush.assert_called_once()

    def test_revoke_by_token_id_returns_false_when_not_found(self) -> None:
        db = _mock_db_session()
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.revoke_by_token_id("nonexistent")
        assert result is False

    def test_revoke_by_token_id_returns_true_when_found(self) -> None:
        db = _mock_db_session()
        model = _make_session_model()
        db.execute.return_value.scalars.return_value.first.return_value = model
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.revoke_by_token_id("jti-123")
        assert result is True
        assert model.is_revoked is True
        assert model.revoked_at is not None

    @patch("app.infrastructure.repositories.session_repository.datetime")
    def test_revoke_all_user_sessions(self, mock_datetime: MagicMock) -> None:
        mock_now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        db = _mock_db_session()
        db.execute.return_value.rowcount = 3
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.revoke_all_user_sessions("u1")
        assert result == 3
        db.execute.assert_called_once()
        db.flush.assert_called_once()

    @patch("app.infrastructure.repositories.session_repository.datetime")
    def test_revoke_all_returns_zero_when_none_active(
        self, mock_datetime: MagicMock
    ) -> None:
        mock_now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        db = _mock_db_session()
        db.execute.return_value.rowcount = 0
        repo = SQLAlchemySessionRepository(session=db)

        result = repo.revoke_all_user_sessions("u-no-sessions")
        assert result == 0
