"""Unit tests for JWTTokenService.

Tests the infrastructure adapter for ITokenService covering:
- Access token creation and claim content
- Refresh token creation and claim content
- Token verification (access and refresh)
- Expired token rejection
- Invalid signature rejection
- Cross-type token rejection (access as refresh, vice-versa)
- Malformed token rejection
- Empty secret key rejection
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
from jose import jwt

from app.core.exceptions import AuthenticationError
from app.infrastructure.services.jwt_token_service import JWTTokenService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SECRET_KEY = "test-secret-key-for-unit-tests-only"
ALT_SECRET_KEY = "different-secret-key-for-signature-tests"


@pytest.fixture
def token_service() -> JWTTokenService:
    """Provide a JWTTokenService with short expiry for fast tests."""
    return JWTTokenService(
        secret_key=SECRET_KEY,
        access_token_expire_minutes=15,
        refresh_token_expire_days=1,
    )


def _make_expired_token(
    subject: str = "user-1",
    token_type: str = "access",
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT that expired 1 hour ago."""
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    if extra_claims:
        claims.update(extra_claims)
    return cast(str, jwt.encode(claims, SECRET_KEY, algorithm="HS256"))


# ---------------------------------------------------------------------------
# Access Token Creation
# ---------------------------------------------------------------------------


class TestCreateAccessToken:
    """Tests for JWTTokenService.create_access_token."""

    def test_returns_non_empty_string(self, token_service: JWTTokenService) -> None:
        """Access token creation returns a non-empty JWT string."""
        token = token_service.create_access_token("user-1", ["admin"])
        assert isinstance(token, str)
        assert len(token) > 0

    def test_contains_expected_claims(self, token_service: JWTTokenService) -> None:
        """Access token embeds sub, roles, type, iat, and exp claims."""
        token = token_service.create_access_token("user-1", ["admin", "analyst"])
        claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        assert claims["sub"] == "user-1"
        assert claims["roles"] == ["admin", "analyst"]
        assert claims["type"] == "access"
        assert "iat" in claims
        assert "exp" in claims

    def test_empty_roles_list(self, token_service: JWTTokenService) -> None:
        """Access token supports empty roles list for users without roles."""
        token = token_service.create_access_token("user-1", [])
        claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert claims["roles"] == []

    def test_expiry_is_in_future(self, token_service: JWTTokenService) -> None:
        """Access token expiry is set in the future."""
        token = token_service.create_access_token("user-1", [])
        claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        exp = datetime.fromtimestamp(claims["exp"], tz=UTC)
        assert exp > datetime.now(UTC)


# ---------------------------------------------------------------------------
# Refresh Token Creation
# ---------------------------------------------------------------------------


class TestCreateRefreshToken:
    """Tests for JWTTokenService.create_refresh_token."""

    def test_returns_non_empty_string(self, token_service: JWTTokenService) -> None:
        """Refresh token creation returns a non-empty JWT string."""
        token = token_service.create_refresh_token("user-1", "jti-abc-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_contains_expected_claims(self, token_service: JWTTokenService) -> None:
        """Refresh token embeds sub, jti, type, iat, and exp claims."""
        token = token_service.create_refresh_token("user-1", "jti-abc-123")
        claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        assert claims["sub"] == "user-1"
        assert claims["jti"] == "jti-abc-123"
        assert claims["type"] == "refresh"
        assert "iat" in claims
        assert "exp" in claims

    def test_expiry_is_in_future(self, token_service: JWTTokenService) -> None:
        """Refresh token expiry is set in the future."""
        token = token_service.create_refresh_token("user-1", "jti-123")
        claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        exp = datetime.fromtimestamp(claims["exp"], tz=UTC)
        assert exp > datetime.now(UTC)


# ---------------------------------------------------------------------------
# Access Token Verification
# ---------------------------------------------------------------------------


class TestVerifyAccessToken:
    """Tests for JWTTokenService.verify_access_token."""

    def test_valid_token_returns_claims(self, token_service: JWTTokenService) -> None:
        """Valid access token verification returns decoded claims dict."""
        token = token_service.create_access_token("user-1", ["admin"])
        claims = token_service.verify_access_token(token)
        assert claims["sub"] == "user-1"
        assert claims["roles"] == ["admin"]
        assert claims["type"] == "access"

    def test_expired_token_raises(self, token_service: JWTTokenService) -> None:
        """Expired access token raises AuthenticationError."""
        token = _make_expired_token(token_type="access")
        with pytest.raises(AuthenticationError):
            token_service.verify_access_token(token)

    def test_wrong_signature_raises(self, token_service: JWTTokenService) -> None:
        """Token signed with a different key raises AuthenticationError."""
        alt_service = JWTTokenService(secret_key=ALT_SECRET_KEY)
        token = alt_service.create_access_token("user-1", ["admin"])
        with pytest.raises(AuthenticationError):
            token_service.verify_access_token(token)

    def test_refresh_token_as_access_raises(
        self, token_service: JWTTokenService
    ) -> None:
        """Using a refresh token for access verification raises error."""
        token = token_service.create_refresh_token("user-1", "jti-123")
        with pytest.raises(AuthenticationError, match="token type"):
            token_service.verify_access_token(token)

    def test_malformed_token_raises(self, token_service: JWTTokenService) -> None:
        """Malformed JWT string raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            token_service.verify_access_token("not.a.valid.jwt")


# ---------------------------------------------------------------------------
# Refresh Token Verification
# ---------------------------------------------------------------------------


class TestVerifyRefreshToken:
    """Tests for JWTTokenService.verify_refresh_token."""

    def test_valid_token_returns_claims(self, token_service: JWTTokenService) -> None:
        """Valid refresh token verification returns decoded claims dict."""
        token = token_service.create_refresh_token("user-1", "jti-abc")
        claims = token_service.verify_refresh_token(token)
        assert claims["sub"] == "user-1"
        assert claims["jti"] == "jti-abc"
        assert claims["type"] == "refresh"

    def test_expired_token_raises(self, token_service: JWTTokenService) -> None:
        """Expired refresh token raises AuthenticationError."""
        token = _make_expired_token(
            token_type="refresh", extra_claims={"jti": "jti-123"}
        )
        with pytest.raises(AuthenticationError):
            token_service.verify_refresh_token(token)

    def test_wrong_signature_raises(self, token_service: JWTTokenService) -> None:
        """Token signed with a different key raises AuthenticationError."""
        alt_service = JWTTokenService(secret_key=ALT_SECRET_KEY)
        token = alt_service.create_refresh_token("user-1", "jti-123")
        with pytest.raises(AuthenticationError):
            token_service.verify_refresh_token(token)

    def test_access_token_as_refresh_raises(
        self, token_service: JWTTokenService
    ) -> None:
        """Using an access token for refresh verification raises error."""
        token = token_service.create_access_token("user-1", [])
        with pytest.raises(AuthenticationError, match="token type"):
            token_service.verify_refresh_token(token)

    def test_malformed_token_raises(self, token_service: JWTTokenService) -> None:
        """Malformed JWT string raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            token_service.verify_refresh_token("garbage-string")


# ---------------------------------------------------------------------------
# Construction Validation
# ---------------------------------------------------------------------------


class TestConstruction:
    """Tests for JWTTokenService constructor validation."""

    def test_empty_secret_key_raises_value_error(self) -> None:
        """Empty secret key is rejected at construction time."""
        with pytest.raises(ValueError, match="secret_key must not be empty"):
            JWTTokenService(secret_key="")

    def test_whitespace_secret_key_raises_value_error(self) -> None:
        """Whitespace-only secret key is rejected at construction time."""
        with pytest.raises(ValueError, match="secret_key must not be empty"):
            JWTTokenService(secret_key="   ")

    def test_custom_expiry_values(self) -> None:
        """Custom expiry durations are respected."""
        service = JWTTokenService(
            secret_key=SECRET_KEY,
            access_token_expire_minutes=5,
            refresh_token_expire_days=30,
        )
        token = service.create_access_token("user-1", [])
        claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        exp = datetime.fromtimestamp(claims["exp"], tz=UTC)
        iat = datetime.fromtimestamp(claims["iat"], tz=UTC)
        delta = exp - iat
        # Allow 2-second tolerance for clock drift during test execution
        assert abs(delta.total_seconds() - 300) < 2
