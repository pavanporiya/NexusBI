"""NexusBI API Layer Dependencies package.

Exports reusable FastAPI dependencies for authentication and authorization.
"""

from app.api.dependencies.auth import (
    get_authorization_service,
    get_current_user,
    get_current_user_use_case,
    get_token_service,
    get_user_repository,
)
from app.api.dependencies.authorization import (
    AllPermissionsDependency,
    AnyPermissionDependency,
    PermissionDependency,
    require_all_permissions,
    require_any_permission,
    require_permission,
)

__all__ = [
    "AllPermissionsDependency",
    "AnyPermissionDependency",
    "PermissionDependency",
    "get_authorization_service",
    "get_current_user",
    "get_current_user_use_case",
    "get_token_service",
    "get_user_repository",
    "require_all_permissions",
    "require_any_permission",
    "require_permission",
]
