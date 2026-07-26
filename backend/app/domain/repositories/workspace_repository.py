"""Workspace repository port interface.

Defines the contract for workspace persistence and retrieval.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.workspace import Workspace


@runtime_checkable
class IWorkspaceRepository(Protocol):
    """Port interface for persisting and fetching Workspace entities."""

    def get_by_id(self, workspace_id: str) -> Workspace | None:
        """Fetch a Workspace by its unique ID."""
        ...

    def get_by_slug(self, organization_id: str, slug: str) -> Workspace | None:
        """Fetch a Workspace by organization ID and slug."""
        ...

    def save(self, workspace: Workspace) -> Workspace:
        """Persist a new Workspace or update an existing one."""
        ...

    def delete(self, workspace_id: str) -> bool:
        """Permanently remove a Workspace by ID."""
        ...

    def list_by_organization_id(
        self, organization_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Workspace], int]:
        """Fetch a paginated list of Workspaces for an Organization with total count."""
        ...

    def list_all(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Workspace], int]:
        """Fetch a paginated list of all Workspaces with total count."""
        ...
