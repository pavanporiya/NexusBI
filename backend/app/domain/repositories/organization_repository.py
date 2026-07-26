"""Organization repository port interface.

Defines the contract for organization persistence and retrieval.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.organization import Organization


@runtime_checkable
class IOrganizationRepository(Protocol):
    """Port interface for persisting and fetching Organization entities."""

    def get_by_id(self, organization_id: str) -> Organization | None:
        """Fetch an Organization by its unique ID."""
        ...

    def get_by_slug(self, slug: str) -> Organization | None:
        """Fetch an Organization by its unique slug."""
        ...

    def save(self, organization: Organization) -> Organization:
        """Persist a new Organization or update an existing one."""
        ...

    def delete(self, organization_id: str) -> bool:
        """Permanently remove an Organization by ID."""
        ...

    def list_all(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Organization], int]:
        """Fetch a paginated list of Organizations with total count."""
        ...
