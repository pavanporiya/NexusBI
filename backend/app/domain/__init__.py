"""NexusBI Domain Layer.

Contains pure business logic, domain entities, port interfaces, and
use case orchestrators. This layer has zero external dependencies —
it must never import from the API or Infrastructure layers.

Architecture Reference:
- phase2_1_repository_blueprint.md Section 2.2
- ADR-005: Clean Architecture
"""

from app.domain.permission_registry import (
    PermissionRegistry,
    find_permission,
    find_role,
    get_default_permissions,
    get_default_roles,
)

__all__ = [
    "PermissionRegistry",
    "find_permission",
    "find_role",
    "get_default_permissions",
    "get_default_roles",
]
