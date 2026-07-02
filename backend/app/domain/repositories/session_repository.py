"""Session repository port interface.

Defines the contract for session persistence, refresh token tracking, and revocation.
"""

from abc import ABC, abstractmethod

from app.domain.entities.session import Session


class ISessionRepository(ABC):
    """Port interface for persisting and managing user Sessions."""

    @abstractmethod
    def get_by_id(self, session_id: str) -> Session | None:
        """Fetch a Session by its primary key ID."""

    @abstractmethod
    def get_by_token_id(self, token_id: str) -> Session | None:
        """Fetch a Session by its associated refresh token ID (JTI)."""

    @abstractmethod
    def get_by_refresh_token(self, refresh_token: str) -> Session | None:
        """Fetch a Session by its raw or signature-matched refresh token."""

    @abstractmethod
    def save(self, session: Session) -> Session:
        """Persist a new Session or update an existing one."""

    @abstractmethod
    def revoke_by_id(self, session_id: str) -> bool:
        """Mark a specific Session as revoked."""

    @abstractmethod
    def revoke_by_token_id(self, token_id: str) -> bool:
        """Mark a specific Session as revoked using its refresh token ID (JTI)."""

    @abstractmethod
    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Mark all active sessions for a user as revoked (e.g. forced logout)."""
