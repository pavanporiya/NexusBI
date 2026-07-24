"""User repository port interface.

Defines the contract for user persistence and retrieval in Clean Architecture.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.user import User


@runtime_checkable
class IUserRepository(Protocol):
    """Port interface for persisting and fetching User entities."""

    def get_by_id(self, user_id: str) -> User | None:
        """Fetch a User by their unique system ID."""
        ...

    def get_by_email(self, email: str) -> User | None:
        """Fetch a User by their unique email address."""
        ...

    def get_by_google_id(self, google_id: str) -> User | None:
        """Fetch a User by their linked Google account ID."""
        ...

    def save(self, user: User) -> User:
        """Persist a new User or update an existing one."""
        ...

    def delete(self, user_id: str) -> bool:
        """Permanently remove a User from persistence."""
        ...
