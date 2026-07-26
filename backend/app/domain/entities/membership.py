"""Membership domain entity.

Represents a user's membership and assigned role within a workspace.
Enforces domain invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.exceptions import DomainValidationError


@dataclass(slots=True)
class Membership:
    """Represents a Workspace Membership domain entity.

    Attributes
    ----------
    id : str
        UUID primary key.
    workspace_id : str
        ID of the workspace.
    user_id : str
        ID of the user.
    role_id : str
        ID of the assigned role.
    joined_at : datetime
        UTC timestamp when the user joined the workspace.
    is_active : bool
        Whether the membership is active.
    """

    id: str
    workspace_id: str
    user_id: str
    role_id: str
    joined_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate membership domain invariants."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Membership id must not be empty")
        if not self.workspace_id or not self.workspace_id.strip():
            raise DomainValidationError("Membership workspace_id must not be empty")
        if not self.user_id or not self.user_id.strip():
            raise DomainValidationError("Membership user_id must not be empty")
        if not self.role_id or not self.role_id.strip():
            raise DomainValidationError("Membership role_id must not be empty")

        self.workspace_id = self.workspace_id.strip()
        self.user_id = self.user_id.strip()
        self.role_id = self.role_id.strip()

    def update_role(self, role_id: str) -> None:
        """Update assigned role in the workspace."""
        stripped = role_id.strip()
        if not stripped:
            raise DomainValidationError("Membership role_id must not be empty")
        self.role_id = stripped

    def set_active_status(self, is_active: bool) -> None:
        """Update active status."""
        self.is_active = is_active
