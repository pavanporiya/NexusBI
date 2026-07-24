"""Authorization service infrastructure implementation.

Provides domain-driven RBAC permission and role evaluation implementing
IAuthorizationService.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.services.interfaces import IAuthorizationService
from app.domain.entities.user import User


class AuthorizationService(IAuthorizationService):
    """Concrete implementation of IAuthorizationService.

    Evaluates authorization decisions against rich domain entities (User, Role,
    Permission). Ensures that inactive users (is_active == False) are denied access
    across all authorization checks.
    """

    def has_permission(self, user: User, permission: str) -> bool:
        """Check if an active user possesses the specified permission.

        Parameters
        ----------
        user : User
            The user entity to evaluate.
        permission : str
            A plain permission name or qualified 'resource:action' string.

        Returns
        -------
        bool
            True if the user is active and has the permission via any assigned role.
        """
        if not user.is_active:
            return False
        return user.has_permission(permission)

    def has_any_permission(self, user: User, permissions: Sequence[str]) -> bool:
        """Check if an active user possesses at least one of the specified permissions.

        Parameters
        ----------
        user : User
            The user entity to evaluate.
        permissions : Sequence[str]
            A sequence of permission names to check.

        Returns
        -------
        bool
            True if user is active and has at least one of the permissions.
        """
        if not user.is_active or not permissions:
            return False
        return any(user.has_permission(perm) for perm in permissions)

    def has_all_permissions(self, user: User, permissions: Sequence[str]) -> bool:
        """Check if an active user possesses all of the specified permissions.

        Parameters
        ----------
        user : User
            The user entity to evaluate.
        permissions : Sequence[str]
            A sequence of permission names to check.

        Returns
        -------
        bool
            True if user is active and has all of the permissions.
        """
        if not user.is_active or not permissions:
            return False
        return all(user.has_permission(perm) for perm in permissions)

    def has_role(self, user: User, role_name: str) -> bool:
        """Check if an active user holds the specified role by name.

        Parameters
        ----------
        user : User
            The user entity to evaluate.
        role_name : str
            The name of the role to check (e.g., 'admin').

        Returns
        -------
        bool
            True if the user is active and holds the role.
        """
        if not user.is_active:
            return False
        return role_name in user.role_names

    def has_any_role(self, user: User, role_names: Sequence[str]) -> bool:
        """Check if an active user holds at least one of the specified roles.

        Parameters
        ----------
        user : User
            The user entity to evaluate.
        role_names : Sequence[str]
            A sequence of role names to check.

        Returns
        -------
        bool
            True if user is active and holds at least one role in role_names.
        """
        if not user.is_active or not role_names:
            return False
        user_roles = set(user.role_names)
        return any(role in user_roles for role in role_names)

    def has_all_roles(self, user: User, role_names: Sequence[str]) -> bool:
        """Check if an active user holds all of the specified roles.

        Parameters
        ----------
        user : User
            The user entity to evaluate.
        role_names : Sequence[str]
            A sequence of role names to check.

        Returns
        -------
        bool
            True if user is active and holds all roles in role_names.
        """
        if not user.is_active or not role_names:
            return False
        user_roles = set(user.role_names)
        return all(role in user_roles for role in role_names)

    def can_access(self, user: User, resource: str, action: str) -> bool:
        """Check if an active user is authorized to perform action on resource.

        Parameters
        ----------
        user : User
            The user entity to evaluate.
        resource : str
            The target resource (e.g., 'dashboard').
        action : str
            The target action (e.g., 'read').

        Returns
        -------
        bool
            True if user is active and has the resource:action permission.
        """
        if not user.is_active:
            return False
        return self.has_permission(user, f"{resource}:{action}")

    def get_user_permissions(self, user: User) -> set[str]:
        """Collect all qualified permission names assigned to an active user.

        Parameters
        ----------
        user : User
            The user entity to inspect.

        Returns
        -------
        set[str]
            Set of all qualified permission names ('resource:action') for an
            active user.
            Returns empty set if user is inactive.
        """
        if not user.is_active:
            return set()
        return set(user.permission_names)

    def get_user_roles(self, user: User) -> set[str]:
        """Collect all role names assigned to an active user.

        Parameters
        ----------
        user : User
            The user entity to inspect.

        Returns
        -------
        set[str]
            Set of all role names assigned to an active user.
            Returns empty set if user is inactive.
        """
        if not user.is_active:
            return set()
        return set(user.role_names)
