"""Application service interfaces.

Defines ports for token generation, password hashing, and OAuth flows.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from app.application.dto.auth_dto import GoogleUserDTO
from app.domain.entities.user import User


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


class IAuthorizationService(ABC):
    """Port interface for RBAC permission and role evaluation service."""

    @abstractmethod
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if an active user possesses the specified permission."""

    @abstractmethod
    def has_any_permission(self, user: User, permissions: Sequence[str]) -> bool:
        """Check if an active user possesses at least one of the specified
        permissions.
        """

    @abstractmethod
    def has_all_permissions(self, user: User, permissions: Sequence[str]) -> bool:
        """Check if an active user possesses all of the specified permissions."""

    @abstractmethod
    def has_role(self, user: User, role_name: str) -> bool:
        """Check if an active user holds the specified role by name."""

    @abstractmethod
    def has_any_role(self, user: User, role_names: Sequence[str]) -> bool:
        """Check if an active user holds at least one of the specified roles."""

    @abstractmethod
    def has_all_roles(self, user: User, role_names: Sequence[str]) -> bool:
        """Check if an active user holds all of the specified roles."""

    @abstractmethod
    def can_access(self, user: User, resource: str, action: str) -> bool:
        """Check if an active user is authorized to perform action on resource."""

    @abstractmethod
    def get_user_permissions(self, user: User) -> set[str]:
        """Collect all qualified permission names assigned to an active user."""

    @abstractmethod
    def get_user_roles(self, user: User) -> set[str]:
        """Collect all role names assigned to an active user."""
