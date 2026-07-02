"""User domain entity.

Represents an identity within the system, either authenticated locally via password
or externally via Google OAuth.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.entities.role import Role


@dataclass
class User:
    """Represents a system user with associated roles and access flags."""

    id: str
    email: str
    hashed_password: str | None = None
    is_active: bool = True
    google_id: str | None = None
    roles: list[Role] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def has_permission(self, permission_name: str) -> bool:
        """Check if any of the user's assigned roles carry the specified permission."""
        return any(role.has_permission(permission_name) for role in self.roles)

    @property
    def permission_names(self) -> list[str]:
        """Collect all permission names assigned to this user."""
        names = set()
        for role in self.roles:
            for perm in role.permissions:
                names.add(perm.name)
        return sorted(names)

    @property
    def role_names(self) -> list[str]:
        """Collect all role names assigned to this user."""
        return [role.name for role in self.roles]
