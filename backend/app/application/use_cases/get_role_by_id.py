"""Get role by ID use case.

Orchestrates loading a specific role by its unique identifier.
"""

from __future__ import annotations

from app.application.dto.role_dto import PermissionDTO, RoleDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.role_repository import IRoleRepository


class GetRoleByIdUseCase:
    """Orchestrates loading a role by unique role ID."""

    def __init__(self, role_repository: IRoleRepository) -> None:
        self._role_repo = role_repository

    def execute(self, role_id: str) -> RoleDTO:
        """Retrieve role details for the given role ID.

        Parameters
        ----------
        role_id : str
            The unique identifier of the role to retrieve.

        Returns
        -------
        RoleDTO
            The role detail data transfer object.

        Raises
        ------
        EntityNotFoundError
            If no role exists with the given role_id.
        """
        role = self._role_repo.get_by_id(role_id)
        if role is None:
            raise EntityNotFoundError("Role", role_id)

        return RoleDTO(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[
                PermissionDTO(
                    id=perm.id,
                    resource=perm.resource,
                    action=perm.action,
                    description=perm.description,
                )
                for perm in role.permissions
            ],
        )
