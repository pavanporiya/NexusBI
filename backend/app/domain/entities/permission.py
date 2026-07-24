"""Permission domain entity.

Represents an action or access privilege on a specific resource within the
platform RBAC system (e.g., resource="dashboard", action="read").

A Permission is modelled as a **frozen value object** — once created it is
immutable, which guarantees referential transparency across the domain layer.

Business Rules
--------------
* A permission is uniquely identified by its ``(resource, action)`` pair.
* The ``qualified_name`` property produces the canonical string form
  ``resource:action`` used for comparison throughout the domain.
* ``name`` is retained as an alias for backward-compatible access patterns
  established in Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Permission:
    """Immutable value object representing a discrete RBAC permission.

    Attributes
    ----------
    id : str
        Unique identifier for the permission.
    resource : str
        The protected resource this permission governs (e.g. ``"dashboard"``).
    action : str
        The allowed operation on the resource (e.g. ``"read"``, ``"write"``).
    description : str | None
        Optional human-readable explanation of the permission.
    """

    id: str
    resource: str
    action: str
    description: str | None = None

    # ------------------------------------------------------------------
    # Backward-compatible alias
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the canonical ``resource:action`` identifier.

        This property maintains backward compatibility with Phase 1 code
        that references ``permission.name``.
        """
        return self.qualified_name

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def qualified_name(self) -> str:
        """Return the canonical ``resource:action`` string form."""
        return f"{self.resource}:{self.action}"

    # ------------------------------------------------------------------
    # Equality / hashing (identity by resource + action)
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """Two permissions are equal when they govern the same resource:action."""
        if not isinstance(other, Permission):
            return NotImplemented
        return self.resource == other.resource and self.action == other.action

    def __hash__(self) -> int:
        return hash((self.resource, self.action))

    def __repr__(self) -> str:
        return (
            f"Permission(id={self.id!r}, resource={self.resource!r}, "
            f"action={self.action!r})"
        )
