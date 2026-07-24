"""Unit tests for authentication use cases.

Tests all five authentication use case orchestrators with mock repositories
and services, validating business logic without infrastructure dependencies:

- RegisterUserUseCase
- LoginUserUseCase
- RefreshTokenUseCase
- LogoutUserUseCase
- GetCurrentUserUseCase
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.application.dto.auth_dto import LoginDTO, RegisterDTO, TokenRefreshDTO
from app.application.use_cases.get_current_user import GetCurrentUserUseCase
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.logout_user import LogoutUserUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.core.exceptions import AuthenticationError, DuplicateEntityError
from app.domain.entities.session import Session
from app.domain.entities.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(
    user_id: str = "user-001",
    email: str = "test@example.com",
    hashed_password: str | None = "$2b$12$fakehash",
    is_active: bool = True,
    roles: list[Any] | None = None,
) -> User:
    """Create a test User entity."""
    return User(
        id=user_id,
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
        roles=roles or [],
    )


def _make_session(
    session_id: str | None = None,
    user_id: str = "user-001",
    token_id: str = "jti-abc",
    refresh_token: str = "refresh-token-value",
    is_revoked: bool = False,
    expired: bool = False,
) -> Session:
    """Create a test Session entity."""
    if expired:
        expires_at = datetime.now(UTC) - timedelta(hours=1)
    else:
        expires_at = datetime.now(UTC) + timedelta(days=7)
    return Session(
        id=session_id or str(uuid.uuid4()),
        user_id=user_id,
        token_id=token_id,
        refresh_token=refresh_token,
        expires_at=expires_at,
        is_revoked=is_revoked,
    )


def _mock_settings() -> MagicMock:
    """Create a mock Settings object with required auth fields."""
    settings = MagicMock()
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
    settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
    return settings


# ═══════════════════════════════════════════════════════════════════════════
# RegisterUserUseCase
# ═══════════════════════════════════════════════════════════════════════════


class TestRegisterUserUseCase:
    """Tests for RegisterUserUseCase orchestration logic."""

    def _build_use_case(
        self,
        user_repo: MagicMock | None = None,
        hasher: MagicMock | None = None,
    ) -> tuple[RegisterUserUseCase, MagicMock, MagicMock]:
        repo = user_repo or MagicMock()
        pw_hasher = hasher or MagicMock()
        uc = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=pw_hasher,
        )
        return uc, repo, pw_hasher

    def test_successful_registration(self) -> None:
        """New user is persisted and a UserDTO is returned."""
        uc, repo, hasher = self._build_use_case()
        repo.get_by_email.return_value = None
        hasher.hash_password.return_value = "$2b$12$hashed"

        saved_user = _make_user(hashed_password="$2b$12$hashed")
        repo.save.return_value = saved_user

        dto = RegisterDTO(email="test@example.com", password="StrongP@ss1")
        result = uc.execute(dto)

        assert result.email == "test@example.com"
        assert result.is_active is True
        hasher.hash_password.assert_called_once_with("StrongP@ss1")
        repo.save.assert_called_once()

    def test_duplicate_email_raises(self) -> None:
        """Registering with an existing email raises DuplicateEntityError."""
        uc, repo, _ = self._build_use_case()
        repo.get_by_email.return_value = _make_user()

        dto = RegisterDTO(email="test@example.com", password="StrongP@ss1")
        with pytest.raises(DuplicateEntityError):
            uc.execute(dto)

    def test_password_hasher_is_called(self) -> None:
        """The password hasher is invoked with the raw password."""
        uc, repo, hasher = self._build_use_case()
        repo.get_by_email.return_value = None
        hasher.hash_password.return_value = "$2b$12$hashed"
        repo.save.return_value = _make_user()

        dto = RegisterDTO(email="new@example.com", password="StrongP@ss1")
        uc.execute(dto)

        hasher.hash_password.assert_called_once_with("StrongP@ss1")

    def test_user_gets_unique_id(self) -> None:
        """Each registered user receives a UUID as their identifier."""
        uc, repo, hasher = self._build_use_case()
        repo.get_by_email.return_value = None
        hasher.hash_password.return_value = "$2b$12$hashed"
        repo.save.side_effect = lambda user: user

        dto = RegisterDTO(email="new@example.com", password="StrongP@ss1")
        result = uc.execute(dto)

        # Validate UUID format
        uuid.UUID(result.id)


# ═══════════════════════════════════════════════════════════════════════════
# LoginUserUseCase
# ═══════════════════════════════════════════════════════════════════════════


class TestLoginUserUseCase:
    """Tests for LoginUserUseCase orchestration logic."""

    def _build_use_case(
        self,
    ) -> tuple[LoginUserUseCase, MagicMock, MagicMock, MagicMock, MagicMock]:
        user_repo = MagicMock()
        session_repo = MagicMock()
        hasher = MagicMock()
        token_svc = MagicMock()
        with patch(
            "app.application.use_cases.login_user.get_settings",
            return_value=_mock_settings(),
        ):
            uc = LoginUserUseCase(
                user_repository=user_repo,
                session_repository=session_repo,
                password_hasher=hasher,
                token_service=token_svc,
            )
        return uc, user_repo, session_repo, hasher, token_svc

    def test_successful_login_returns_tokens(self) -> None:
        """Valid credentials return a TokenDTO with access and refresh tokens."""
        uc, user_repo, session_repo, hasher, token_svc = self._build_use_case()
        user = _make_user()
        user_repo.get_by_email.return_value = user
        hasher.verify_password.return_value = True
        token_svc.create_access_token.return_value = "access-jwt"
        token_svc.create_refresh_token.return_value = "refresh-jwt"

        dto = LoginDTO(email="test@example.com", password="StrongP@ss1")
        result = uc.execute(dto)

        assert result.access_token == "access-jwt"
        assert result.refresh_token == "refresh-jwt"
        assert result.token_type == "Bearer"
        session_repo.save.assert_called_once()

    def test_unknown_email_raises(self) -> None:
        """Login with non-existent email raises AuthenticationError."""
        uc, user_repo, *_ = self._build_use_case()
        user_repo.get_by_email.return_value = None

        dto = LoginDTO(email="unknown@example.com", password="StrongP@ss1")
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            uc.execute(dto)

    def test_wrong_password_raises(self) -> None:
        """Login with wrong password raises AuthenticationError."""
        uc, user_repo, _, hasher, _ = self._build_use_case()
        user_repo.get_by_email.return_value = _make_user()
        hasher.verify_password.return_value = False

        dto = LoginDTO(email="test@example.com", password="WrongP@ss1")
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            uc.execute(dto)

    def test_inactive_user_raises(self) -> None:
        """Login by a disabled user raises AuthenticationError."""
        uc, user_repo, *_ = self._build_use_case()
        user_repo.get_by_email.return_value = _make_user(is_active=False)

        dto = LoginDTO(email="test@example.com", password="StrongP@ss1")
        with pytest.raises(AuthenticationError, match="disabled"):
            uc.execute(dto)

    def test_oauth_only_user_raises(self) -> None:
        """OAuth-only user (no password hash) raises AuthenticationError."""
        uc, user_repo, *_ = self._build_use_case()
        user_repo.get_by_email.return_value = _make_user(hashed_password=None)

        dto = LoginDTO(email="test@example.com", password="StrongP@ss1")
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            uc.execute(dto)

    def test_session_saved_with_client_metadata(self) -> None:
        """Session stores client IP and user agent when provided."""
        uc, user_repo, session_repo, hasher, token_svc = self._build_use_case()
        user_repo.get_by_email.return_value = _make_user()
        hasher.verify_password.return_value = True
        token_svc.create_access_token.return_value = "access-jwt"
        token_svc.create_refresh_token.return_value = "refresh-jwt"

        dto = LoginDTO(email="test@example.com", password="StrongP@ss1")
        uc.execute(dto, client_ip="192.168.1.1", user_agent="TestBrowser/1.0")

        saved_session = session_repo.save.call_args[0][0]
        assert saved_session.client_ip == "192.168.1.1"
        assert saved_session.user_agent == "TestBrowser/1.0"

    def test_access_token_created_with_user_roles(self) -> None:
        """Access token is created with the user's role names."""
        uc, user_repo, _, hasher, token_svc = self._build_use_case()
        user = _make_user()
        user_repo.get_by_email.return_value = user
        hasher.verify_password.return_value = True
        token_svc.create_access_token.return_value = "access-jwt"
        token_svc.create_refresh_token.return_value = "refresh-jwt"

        dto = LoginDTO(email="test@example.com", password="StrongP@ss1")
        uc.execute(dto)

        token_svc.create_access_token.assert_called_once_with(
            subject=user.id,
            roles=user.role_names,
        )


# ═══════════════════════════════════════════════════════════════════════════
# RefreshTokenUseCase
# ═══════════════════════════════════════════════════════════════════════════


class TestRefreshTokenUseCase:
    """Tests for RefreshTokenUseCase orchestration logic."""

    def _build_use_case(
        self,
    ) -> tuple[RefreshTokenUseCase, MagicMock, MagicMock, MagicMock]:
        user_repo = MagicMock()
        session_repo = MagicMock()
        token_svc = MagicMock()
        with patch(
            "app.application.use_cases.refresh_token.get_settings",
            return_value=_mock_settings(),
        ):
            uc = RefreshTokenUseCase(
                user_repository=user_repo,
                session_repository=session_repo,
                token_service=token_svc,
            )
        return uc, user_repo, session_repo, token_svc

    def test_successful_rotation(self) -> None:
        """Valid refresh rotates: revokes old session, creates new one."""
        uc, user_repo, session_repo, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.return_value = {
            "sub": "user-001",
            "jti": "jti-abc",
        }
        session_repo.get_by_token_id.return_value = _make_session()
        user_repo.get_by_id.return_value = _make_user()
        token_svc.create_access_token.return_value = "new-access"
        token_svc.create_refresh_token.return_value = "new-refresh"

        dto = TokenRefreshDTO(refresh_token="old-refresh")
        result = uc.execute(dto)

        assert result.access_token == "new-access"
        assert result.refresh_token == "new-refresh"
        session_repo.revoke_by_token_id.assert_called_once_with("jti-abc")
        session_repo.save.assert_called_once()

    def test_reuse_detection_revokes_all(self) -> None:
        """Reused (already-revoked) token triggers full session revocation."""
        uc, _, session_repo, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.return_value = {
            "sub": "user-001",
            "jti": "jti-abc",
        }
        session_repo.get_by_token_id.return_value = _make_session(is_revoked=True)

        dto = TokenRefreshDTO(refresh_token="stolen-refresh")
        with pytest.raises(AuthenticationError, match="[Cc]ompromised"):
            uc.execute(dto)

        session_repo.revoke_all_user_sessions.assert_called_once_with("user-001")

    def test_expired_session_raises(self) -> None:
        """Expired session raises AuthenticationError."""
        uc, _, session_repo, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.return_value = {
            "sub": "user-001",
            "jti": "jti-abc",
        }
        session_repo.get_by_token_id.return_value = _make_session(expired=True)

        dto = TokenRefreshDTO(refresh_token="expired-refresh")
        with pytest.raises(AuthenticationError, match="invalid or expired"):
            uc.execute(dto)

    def test_invalid_token_raises(self) -> None:
        """Invalid refresh JWT raises AuthenticationError."""
        uc, _, _, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.side_effect = Exception("bad token")

        dto = TokenRefreshDTO(refresh_token="bad-jwt")
        with pytest.raises(AuthenticationError, match="Invalid refresh token"):
            uc.execute(dto)

    def test_inactive_user_raises(self) -> None:
        """Refresh for an inactive user raises AuthenticationError."""
        uc, user_repo, session_repo, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.return_value = {
            "sub": "user-001",
            "jti": "jti-abc",
        }
        session_repo.get_by_token_id.return_value = _make_session()
        user_repo.get_by_id.return_value = _make_user(is_active=False)

        dto = TokenRefreshDTO(refresh_token="valid-refresh")
        with pytest.raises(AuthenticationError, match="inactive"):
            uc.execute(dto)

    def test_missing_session_raises(self) -> None:
        """Refresh with no matching session raises AuthenticationError."""
        uc, _, session_repo, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.return_value = {
            "sub": "user-001",
            "jti": "jti-unknown",
        }
        session_repo.get_by_token_id.return_value = None

        dto = TokenRefreshDTO(refresh_token="orphan-refresh")
        with pytest.raises(AuthenticationError, match="invalid or expired"):
            uc.execute(dto)

    def test_malformed_claims_raises(self) -> None:
        """Refresh token with missing claims raises AuthenticationError."""
        uc, _, _, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.return_value = {}

        dto = TokenRefreshDTO(refresh_token="malformed-refresh")
        with pytest.raises(AuthenticationError, match="[Mm]alformed"):
            uc.execute(dto)

    def test_new_session_inherits_client_metadata(self) -> None:
        """New session inherits client_ip and user_agent from old session."""
        uc, user_repo, session_repo, token_svc = self._build_use_case()
        old_session = _make_session()
        old_session.client_ip = "10.0.0.1"
        old_session.user_agent = "OldBrowser/1.0"

        token_svc.verify_refresh_token.return_value = {
            "sub": "user-001",
            "jti": "jti-abc",
        }
        session_repo.get_by_token_id.return_value = old_session
        user_repo.get_by_id.return_value = _make_user()
        token_svc.create_access_token.return_value = "new-access"
        token_svc.create_refresh_token.return_value = "new-refresh"

        dto = TokenRefreshDTO(refresh_token="old-refresh")
        uc.execute(dto)

        new_session = session_repo.save.call_args[0][0]
        assert new_session.client_ip == "10.0.0.1"
        assert new_session.user_agent == "OldBrowser/1.0"


# ═══════════════════════════════════════════════════════════════════════════
# LogoutUserUseCase
# ═══════════════════════════════════════════════════════════════════════════


class TestLogoutUserUseCase:
    """Tests for LogoutUserUseCase orchestration logic."""

    def _build_use_case(self) -> tuple[LogoutUserUseCase, MagicMock, MagicMock]:
        session_repo = MagicMock()
        token_svc = MagicMock()
        uc = LogoutUserUseCase(
            session_repository=session_repo,
            token_service=token_svc,
        )
        return uc, session_repo, token_svc

    def test_successful_logout(self) -> None:
        """Valid refresh token triggers session revocation by token ID."""
        uc, session_repo, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.return_value = {"jti": "jti-abc"}

        uc.execute("valid-refresh-token")

        session_repo.revoke_by_token_id.assert_called_once_with("jti-abc")

    def test_invalid_token_raises(self) -> None:
        """Invalid refresh token raises AuthenticationError on logout."""
        uc, _, token_svc = self._build_use_case()
        token_svc.verify_refresh_token.side_effect = Exception("decode failure")

        with pytest.raises(AuthenticationError, match="logout"):
            uc.execute("bad-refresh-token")


# ═══════════════════════════════════════════════════════════════════════════
# GetCurrentUserUseCase
# ═══════════════════════════════════════════════════════════════════════════


class TestGetCurrentUserUseCase:
    """Tests for GetCurrentUserUseCase orchestration logic."""

    def _build_use_case(self) -> tuple[GetCurrentUserUseCase, MagicMock, MagicMock]:
        user_repo = MagicMock()
        token_svc = MagicMock()
        uc = GetCurrentUserUseCase(
            user_repository=user_repo,
            token_service=token_svc,
        )
        return uc, user_repo, token_svc

    def test_successful_user_retrieval(self) -> None:
        """Valid access token returns the authenticated user's profile."""
        uc, user_repo, token_svc = self._build_use_case()
        token_svc.verify_access_token.return_value = {"sub": "user-001"}
        user_repo.get_by_id.return_value = _make_user()

        result = uc.execute("valid-access-token")

        assert result.id == "user-001"
        assert result.email == "test@example.com"
        assert result.is_active is True
        user_repo.get_by_id.assert_called_once_with("user-001")

    def test_invalid_token_raises(self) -> None:
        """Invalid access token raises AuthenticationError."""
        uc, _, token_svc = self._build_use_case()
        token_svc.verify_access_token.side_effect = Exception("decode failure")

        with pytest.raises(AuthenticationError, match="Invalid access token"):
            uc.execute("bad-access-token")

    def test_missing_sub_claim_raises(self) -> None:
        """Access token without sub claim raises AuthenticationError."""
        uc, _, token_svc = self._build_use_case()
        token_svc.verify_access_token.return_value = {"roles": ["admin"]}

        with pytest.raises(AuthenticationError, match="[Mm]alformed"):
            uc.execute("no-sub-token")

    def test_nonexistent_user_raises(self) -> None:
        """Token for a deleted user raises AuthenticationError."""
        uc, user_repo, token_svc = self._build_use_case()
        token_svc.verify_access_token.return_value = {"sub": "deleted-user"}
        user_repo.get_by_id.return_value = None

        with pytest.raises(AuthenticationError, match="not found"):
            uc.execute("valid-token-for-deleted-user")

    def test_inactive_user_raises(self) -> None:
        """Token for a disabled user raises AuthenticationError."""
        uc, user_repo, token_svc = self._build_use_case()
        token_svc.verify_access_token.return_value = {"sub": "user-001"}
        user_repo.get_by_id.return_value = _make_user(is_active=False)

        with pytest.raises(AuthenticationError, match="disabled"):
            uc.execute("valid-token-for-disabled-user")

    def test_returns_correct_dto_fields(self) -> None:
        """UserDTO contains all expected fields from the user entity."""
        uc, user_repo, token_svc = self._build_use_case()
        token_svc.verify_access_token.return_value = {"sub": "user-001"}
        user = _make_user()
        user_repo.get_by_id.return_value = user

        result = uc.execute("valid-access-token")

        assert result.id == user.id
        assert result.email == str(user.email)
        assert result.is_active == user.is_active
        assert result.roles == user.role_names
        assert result.permissions == user.permission_names
        assert result.created_at == user.created_at
        assert result.updated_at == user.updated_at
