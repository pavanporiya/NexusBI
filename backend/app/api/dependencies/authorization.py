"""Authorization FastAPI dependencies.

Provides reusable dependency factories for enforcing permission constraints
across FastAPI routes:
- require_permission(permission)
- require_any_permission(permissions)
- require_all_permissions(permissions)

Architecture Reference:
- Dependency Flow: FastAPI Dependency -> Authorization Service -> Domain
- Uses existing AuthorizationService (IAuthorizationService)
- Uses existing GetCurrentUser use case
- Strictly orchestrates evaluation with zero authorization logic in dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import get_authorization_service, get_current_user
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import AuthorizationError
from app.domain.entities.user import User


class PermissionDependency:
    """FastAPI dependency for requiring a single permission."""

    def __init__(self, permission: str) -> None:
        self.permission = permission

    def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
        auth_service: Annotated[
            IAuthorizationService, Depends(get_authorization_service)
        ],
    ) -> User:
        """Evaluate required permission for the current active user.

        Parameters
        ----------
        current_user : User
            The authenticated user entity resolved from get_current_user.
        auth_service : IAuthorizationService
            The authorization service implementation.

        Returns
        -------
        User
            The authenticated user entity if authorized.

        Raises
        ------
        AuthorizationError
            If the user lacks the required permission.
        """
        if not auth_service.has_permission(current_user, self.permission):
            raise AuthorizationError(
                message="Permission denied",
                detail=f"Required permission: '{self.permission}'",
            )
        return current_user


class AnyPermissionDependency:
    """FastAPI dependency for requiring at least one of specified permissions."""

    def __init__(self, permissions: Sequence[str]) -> None:
        self.permissions = list(permissions)

    def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
        auth_service: Annotated[
            IAuthorizationService, Depends(get_authorization_service)
        ],
    ) -> User:
        """Evaluate if user possesses at least one of the specified permissions.

        Parameters
        ----------
        current_user : User
            The authenticated user entity resolved from get_current_user.
        auth_service : IAuthorizationService
            The authorization service implementation.

        Returns
        -------
        User
            The authenticated user entity if authorized.

        Raises
        ------
        AuthorizationError
            If the user lacks all specified permissions.
        """
        if not auth_service.has_any_permission(current_user, self.permissions):
            raise AuthorizationError(
                message="Permission denied",
                detail=f"Required at least one of permissions: {self.permissions}",
            )
        return current_user


class AllPermissionsDependency:
    """FastAPI dependency for requiring all specified permissions."""

    def __init__(self, permissions: Sequence[str]) -> None:
        self.permissions = list(permissions)

    def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
        auth_service: Annotated[
            IAuthorizationService, Depends(get_authorization_service)
        ],
    ) -> User:
        """Evaluate if user possesses all of the specified permissions.

        Parameters
        ----------
        current_user : User
            The authenticated user entity resolved from get_current_user.
        auth_service : IAuthorizationService
            The authorization service implementation.

        Returns
        -------
        User
            The authenticated user entity if authorized.

        Raises
        ------
        AuthorizationError
            If the user lacks any of the specified permissions.
        """
        if not auth_service.has_all_permissions(current_user, self.permissions):
            raise AuthorizationError(
                message="Permission denied",
                detail=f"Required all permissions: {self.permissions}",
            )
        return current_user


def require_permission(permission: str) -> PermissionDependency:
    """Create a FastAPI dependency requiring a specific permission.

    Parameters
    ----------
    permission : str
        The permission name (or 'resource:action') required to access the route.

    Returns
    -------
    PermissionDependency
        A callable dependency for FastAPI Depends().
    """
    return PermissionDependency(permission)


def require_any_permission(
    permissions: Sequence[str],
) -> AnyPermissionDependency:
    """Create a FastAPI dependency requiring at least one of specified permissions.

    Parameters
    ----------
    permissions : Sequence[str]
        A sequence of permission names where possessing at least one grants access.

    Returns
    -------
    AnyPermissionDependency
        A callable dependency for FastAPI Depends().
    """
    return AnyPermissionDependency(permissions)


def require_all_permissions(
    permissions: Sequence[str],
) -> AllPermissionsDependency:
    """Create a FastAPI dependency requiring all of specified permissions.

    Parameters
    ----------
    permissions : Sequence[str]
        A sequence of permission names where all must be possessed for access.

    Returns
    -------
    AllPermissionsDependency
        A callable dependency for FastAPI Depends().
    """
    return AllPermissionsDependency(permissions)
