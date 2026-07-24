"""Role repository port interface.

Defines the contract for role persistence and retrieval in Clean Architecture.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role


@runtime_checkable
class IRoleRepository(Protocol):
    """Port interface for fetching and persisting Role entities."""

    def get_all(self) -> list[Role]:
        """Fetch all roles."""
        ...

    def get_by_id(self, role_id: str) -> Role | None:
        """Fetch a role by its unique system ID."""
        ...

    def get_by_name(self, name: str) -> Role | None:
        """Fetch a role by its unique name."""
        ...

    def get_permissions_by_ids(self, permission_ids: list[str]) -> list[Permission]:
        """Fetch permission entities matching given permission IDs or names."""
        ...

    def save(self, role: Role) -> Role:
        """Persist (create or update) a role domain entity."""
        ...

    def delete(self, role_id: str) -> bool:
        """Delete a role by its unique system ID."""
        ...
