"""User domain entity.

Represents an identity within the system, either authenticated locally via
password or externally via Google OAuth. This is a **rich domain entity**
whose methods enforce business invariants directly.

Business Rules
--------------
* ``email`` must be non-empty.
* ``password_hash`` must be non-empty for password-based auth changes.
* A user can only be verified once (idempotent).
* Activate / deactivate are idempotent operations.
* Duplicate role assignment (by role ``id``) is silently ignored.
* ``has_permission`` traverses all assigned roles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.entities.role import Role


@dataclass(slots=True)
class User:
    """Represents a system user with associated roles and access flags.

    Attributes
    ----------
    id : str
        UUID primary key.
    email : str
        Unique email address used for login.
    full_name : str | None
        Optional display name for the user.
    hashed_password : str | None
        Bcrypt hash; ``None`` for OAuth-only accounts.
    is_active : bool
        Whether the account is enabled for login.
    is_verified : bool
        Whether the user has completed email verification.
    google_id : str | None
        Linked Google OAuth subject identifier.
    roles : list[Role]
        RBAC roles assigned to this user.
    created_at : datetime
        UTC timestamp when the account was created.
    updated_at : datetime
        UTC timestamp of the most recent modification.
    """

    id: str
    email: str
    full_name: str | None = None
    hashed_password: str | None = None
    is_active: bool = True
    is_verified: bool = False
    google_id: str | None = None
    roles: list[Role] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # ------------------------------------------------------------------
    # Invariant validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """Validate domain invariants on construction."""
        if not self.email or not self.email.strip():
            raise ValueError("User email must not be empty")

    # ------------------------------------------------------------------
    # Lifecycle mutations
    # ------------------------------------------------------------------

    def activate(self) -> None:
        """Enable the user account for login.

        Idempotent — calling on an already-active user is a no-op.
        """
        if not self.is_active:
            self.is_active = True
            self._touch()

    def deactivate(self) -> None:
        """Disable the user account, preventing further logins.

        Idempotent — calling on an already-inactive user is a no-op.
        """
        if self.is_active:
            self.is_active = False
            self._touch()

    def verify_email(self) -> None:
        """Mark the user's email address as verified.

        Idempotent — calling on an already-verified user is a no-op.
        """
        if not self.is_verified:
            self.is_verified = True
            self._touch()

    # ------------------------------------------------------------------
    # Credential management
    # ------------------------------------------------------------------

    def change_password(self, new_password_hash: str) -> None:
        """Replace the stored password hash.

        Parameters
        ----------
        new_password_hash : str
            The pre-hashed new password (hashing is an infrastructure concern).

        Raises
        ------
        ValueError
            If *new_password_hash* is empty.
        """
        if not new_password_hash or not new_password_hash.strip():
            raise ValueError("Password hash must not be empty")
        self.hashed_password = new_password_hash
        self._touch()

    # ------------------------------------------------------------------
    # Role management
    # ------------------------------------------------------------------

    def assign_role(self, role: Role) -> None:
        """Assign an RBAC role to this user.

        Parameters
        ----------
        role : Role
            The role to assign.

        Notes
        -----
        Duplicate role assignment (same ``id``) is silently ignored.
        """
        if not any(r.id == role.id for r in self.roles):
            self.roles.append(role)
            self._touch()

    def remove_role(self, role_id: str) -> None:
        """Remove an assigned role by its identifier.

        Parameters
        ----------
        role_id : str
            The ``id`` of the role to remove.

        Notes
        -----
        If the role is not present this is a safe no-op.
        """
        before = len(self.roles)
        self.roles = [r for r in self.roles if r.id != role_id]
        if len(self.roles) != before:
            self._touch()

    def has_permission(self, permission_name: str) -> bool:
        """Check if any of the user's assigned roles carry the specified permission.

        Parameters
        ----------
        permission_name : str
            A plain name or ``resource:action`` qualified name.

        Returns
        -------
        bool
            ``True`` if at least one assigned role contains the permission.
        """
        return any(role.has_permission(permission_name) for role in self.roles)

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def permission_names(self) -> list[str]:
        """Collect all qualified permission names assigned to this user."""
        names: set[str] = set()
        for role in self.roles:
            for perm in role.permissions:
                names.add(perm.qualified_name)
        return sorted(names)

    @property
    def role_names(self) -> list[str]:
        """Collect all role names assigned to this user."""
        return [role.name for role in self.roles]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _touch(self) -> None:
        """Bump the ``updated_at`` timestamp to the current UTC time."""
        self.updated_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, email={self.email!r}, "
            f"is_active={self.is_active}, is_verified={self.is_verified})"
        )
