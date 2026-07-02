"""User repository port interface.

Defines the contract for user persistence and retrieval in Clean Architecture.
"""

from abc import ABC, abstractmethod

from app.domain.entities.user import User


class IUserRepository(ABC):
    """Port interface for persisting and fetching User entities."""

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        """Fetch a User by their unique system ID."""

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Fetch a User by their unique email address."""

    @abstractmethod
    def get_by_google_id(self, google_id: str) -> User | None:
        """Fetch a User by their linked Google account ID."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Persist a new User or update an existing one."""

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Permanently remove a User from persistence."""
