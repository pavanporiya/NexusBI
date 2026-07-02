"""Role domain entity.

Groups permissions together to represent a user role (e.g., CEO, Analyst, Admin).
"""

from dataclasses import dataclass, field

from app.domain.entities.permission import Permission


@dataclass
class Role:
    """Represents a user role containing associated permissions."""

    id: str
    name: str
    description: str | None = None
    permissions: list[Permission] = field(default_factory=list)

    def has_permission(self, permission_name: str) -> bool:
        """Check if this role possesses the specified permission."""
        return any(p.name == permission_name for p in self.permissions)
