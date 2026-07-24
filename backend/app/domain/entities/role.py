"""Role domain entity.

Groups permissions together to represent a user role (e.g., CEO, Analyst,
Admin). A Role is a **rich domain entity** that encapsulates permission
management logic.

Business Rules
--------------
* A role name must be non-empty.
* Duplicate permissions (by ``resource:action``) are silently ignored on add.
* Removing a non-existent permission is a safe no-op.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.entities.permission import Permission


@dataclass(slots=True)
class Role:
    """Represents a user role containing associated permissions.

    Attributes
    ----------
    id : str
        Unique identifier for the role.
    name : str
        Human-readable role name (e.g. ``"admin"``, ``"analyst"``).
    description : str | None
        Optional explanation of the role's purpose.
    permissions : list[Permission]
        The set of RBAC permissions granted to holders of this role.
    """

    id: str
    name: str
    description: str | None = None
    permissions: list[Permission] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Invariant validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """Validate domain invariants on construction."""
        if not self.name or not self.name.strip():
            raise ValueError("Role name must not be empty")

    # ------------------------------------------------------------------
    # Permission management
    # ------------------------------------------------------------------

    def add_permission(self, permission: Permission) -> None:
        """Add a permission to this role if it is not already present.

        Parameters
        ----------
        permission : Permission
            The permission to grant.

        Notes
        -----
        Duplicate permissions (equal by ``resource:action``) are silently
        ignored to preserve the set invariant.
        """
        if not self.contains_permission(permission.qualified_name):
            self.permissions.append(permission)

    def remove_permission(self, qualified_name: str) -> None:
        """Remove a permission by its ``resource:action`` qualified name.

        Parameters
        ----------
        qualified_name : str
            The ``resource:action`` identifier of the permission to remove.

        Notes
        -----
        If the permission is not present this is a safe no-op.
        """
        self.permissions = [
            p for p in self.permissions if p.qualified_name != qualified_name
        ]

    def contains_permission(self, qualified_name: str) -> bool:
        """Check whether this role contains the given permission.

        Parameters
        ----------
        qualified_name : str
            The ``resource:action`` identifier to look up.

        Returns
        -------
        bool
            ``True`` if the permission is present in this role.
        """
        return any(p.qualified_name == qualified_name for p in self.permissions)

    # ------------------------------------------------------------------
    # Backward-compatible alias
    # ------------------------------------------------------------------

    def has_permission(self, permission_name: str) -> bool:
        """Check if this role possesses the specified permission.

        This method retains backward compatibility with Phase 1 callers
        that pass either a plain ``name`` or a ``resource:action`` string.
        """
        return any(
            p.name == permission_name or p.qualified_name == permission_name
            for p in self.permissions
        )

    def __repr__(self) -> str:
        perm_count = len(self.permissions)
        return f"Role(id={self.id!r}, name={self.name!r}, permissions={perm_count})"
