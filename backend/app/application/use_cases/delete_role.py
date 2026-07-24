"""Delete role use case.

Orchestrates deletion of custom RBAC roles while protecting default system roles.
"""

from __future__ import annotations

from app.core.exceptions import BusinessRuleViolationError, EntityNotFoundError
from app.domain.permission_registry import DEFAULT_ROLES
from app.domain.repositories.role_repository import IRoleRepository

PROTECTED_ROLE_IDS: set[str] = {r.id for r in DEFAULT_ROLES}
PROTECTED_ROLE_NAMES: set[str] = {r.name.strip().lower() for r in DEFAULT_ROLES}


class DeleteRoleUseCase:
    """Orchestrates deleting a non-system RBAC role."""

    def __init__(self, role_repository: IRoleRepository) -> None:
        self._role_repo = role_repository

    def execute(self, role_id: str) -> None:
        """Delete an existing role by ID.

        Parameters
        ----------
        role_id : str
            Unique identifier of the role to delete.

        Raises
        ------
        EntityNotFoundError
            If no role exists with the given ID.
        BusinessRuleViolationError
            If attempting to delete a protected system/default role.
        """
        role = self._role_repo.get_by_id(role_id)
        if role is None:
            raise EntityNotFoundError("Role", role_id)

        if (
            role.id in PROTECTED_ROLE_IDS
            or role.name.strip().lower() in PROTECTED_ROLE_NAMES
        ):
            raise BusinessRuleViolationError(
                rule="Protected default role deletion",
                detail=f"System default role '{role.name}' cannot be deleted.",
            )

        self._role_repo.delete(role_id)
