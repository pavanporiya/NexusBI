"""JWT token service adapter.

Implements the ``ITokenService`` application port using ``python-jose``
for HS256-signed JWT creation, verification, and claim extraction.

Token Types
-----------
Two distinct token types are issued, each with a ``type`` claim to prevent
cross-use attacks (e.g. using a refresh token as an access token):

- **access**: Short-lived, carries ``sub`` (user ID) and ``roles``.
- **refresh**: Longer-lived, carries ``sub`` and ``jti`` (unique session ID).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt

from app.application.services.interfaces import ITokenService
from app.core.exceptions import AuthenticationError

_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"
_ALGORITHM = "HS256"


class JWTTokenService(ITokenService):
    """HS256 JWT token service backed by python-jose.

    Parameters
    ----------
    secret_key : str
        The HMAC secret used for signing and verification.
    access_token_expire_minutes : int, default=60
        Lifetime of access tokens in minutes.
    refresh_token_expire_days : int, default=7
        Lifetime of refresh tokens in days.
    """

    def __init__(
        self,
        secret_key: str,
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
    ) -> None:
        if not secret_key or not secret_key.strip():
            raise ValueError("JWT secret_key must not be empty")
        self._secret_key = secret_key
        self._access_expire_minutes = access_token_expire_minutes
        self._refresh_expire_days = refresh_token_expire_days

    def create_access_token(self, subject: str, roles: list[str]) -> str:
        """Create a signed JWT access token.

        Claims
        ------
        - ``sub``: User identifier
        - ``roles``: List of role names
        - ``type``: ``"access"``
        - ``iat``: Issued-at UTC timestamp
        - ``exp``: Expiration UTC timestamp
        """
        now = datetime.now(UTC)
        claims: dict[str, Any] = {
            "sub": subject,
            "roles": roles,
            "type": _TOKEN_TYPE_ACCESS,
            "iat": now,
            "exp": now + timedelta(minutes=self._access_expire_minutes),
        }
        return cast(str, jwt.encode(claims, self._secret_key, algorithm=_ALGORITHM))

    def create_refresh_token(self, subject: str, token_id: str) -> str:
        """Create a signed JWT refresh token.

        Claims
        ------
        - ``sub``: User identifier
        - ``jti``: Unique token ID for rotation tracking
        - ``type``: ``"refresh"``
        - ``iat``: Issued-at UTC timestamp
        - ``exp``: Expiration UTC timestamp
        """
        now = datetime.now(UTC)
        claims: dict[str, Any] = {
            "sub": subject,
            "jti": token_id,
            "type": _TOKEN_TYPE_REFRESH,
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expire_days),
        }
        return cast(str, jwt.encode(claims, self._secret_key, algorithm=_ALGORITHM))

    def verify_access_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT access token.

        Raises
        ------
        AuthenticationError
            If the token is invalid, expired, or is not an access token.
        """
        claims = self._decode(token)
        if claims.get("type") != _TOKEN_TYPE_ACCESS:
            raise AuthenticationError(
                "Invalid token type",
                detail="Expected an access token.",
            )
        return claims

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT refresh token.

        Raises
        ------
        AuthenticationError
            If the token is invalid, expired, or is not a refresh token.
        """
        claims = self._decode(token)
        if claims.get("type") != _TOKEN_TYPE_REFRESH:
            raise AuthenticationError(
                "Invalid token type",
                detail="Expected a refresh token.",
            )
        return claims

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _decode(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token.

        Raises
        ------
        AuthenticationError
            If the token cannot be decoded or has expired.
        """
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                self._secret_key,
                algorithms=[_ALGORITHM],
            )
            return claims
        except JWTError as exc:
            raise AuthenticationError(
                "Invalid token",
                detail=str(exc),
            ) from exc
