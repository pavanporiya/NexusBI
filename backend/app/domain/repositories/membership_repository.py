"""Membership repository port interface.

Defines the contract for workspace membership persistence and retrieval.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.membership import Membership


@runtime_checkable
class IMembershipRepository(Protocol):
    """Port interface for persisting and fetching Workspace Membership entities."""

    def get_by_id(self, membership_id: str) -> Membership | None:
        """Fetch a Membership by its unique ID."""
        ...

    def get_by_workspace_and_user(
        self, workspace_id: str, user_id: str
    ) -> Membership | None:
        """Fetch a Membership by workspace ID and user ID."""
        ...

    def save(self, membership: Membership) -> Membership:
        """Persist a new Membership or update an existing one."""
        ...

    def delete(self, membership_id: str) -> bool:
        """Permanently remove a Membership by ID."""
        ...

    def list_by_workspace_id(
        self, workspace_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Membership], int]:
        """Fetch a paginated list of Memberships in a workspace with total count."""
        ...

    def list_by_user_id(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Membership], int]:
        """Fetch a paginated list of Memberships for a user across workspaces."""
        ...
