"""Application service interfaces.

Defines ports for token generation, password hashing, and OAuth flows.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.application.dto.auth_dto import GoogleUserDTO


class IPasswordHasher(ABC):
    """Port interface for secure password operations."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Generate a cryptographically secure hash of the password."""

    @abstractmethod
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify the password matches the given hash."""


class ITokenService(ABC):
    """Port interface for token creation and verification operations."""

    @abstractmethod
    def create_access_token(self, subject: str, roles: list[str]) -> str:
        """Create a signed JWT access token for a subject with role scopes."""

    @abstractmethod
    def create_refresh_token(self, subject: str, token_id: str) -> str:
        """Create a signed JWT refresh token with a unique ID (jti)."""

    @abstractmethod
    def verify_access_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT access token, returning its claims."""

    @abstractmethod
    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT refresh token, returning its claims."""


class IGoogleOAuthService(ABC):
    """Port interface for Google OAuth authentication provider client."""

    @abstractmethod
    def verify_auth_code(self, code: str, redirect_uri: str) -> GoogleUserDTO:
        """Exchange authorization code for user profile info from Google OIDC."""
