"""Permission domain entity.

Represents an action or access privilege within the platform (e.g., allow_chat).
"""

from dataclasses import dataclass


@dataclass
class Permission:
    """Represents a discrete RBAC permission."""

    id: str
    name: str
    description: str | None = None
