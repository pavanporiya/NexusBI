"""Get all roles use case.

Orchestrates listing all system roles and their permissions.
"""

from __future__ import annotations

from app.application.dto.role_dto import PermissionDTO, RoleDTO
from app.domain.repositories.role_repository import IRoleRepository


class GetRolesUseCase:
    """Orchestrates retrieving all roles."""

    def __init__(self, role_repository: IRoleRepository) -> None:
        self._role_repo = role_repository

    def execute(self) -> list[RoleDTO]:
        """Retrieve all system roles with assigned permissions.

        Returns
        -------
        list[RoleDTO]
            List of role data transfer objects.
        """
        roles = self._role_repo.get_all()
        return [
            RoleDTO(
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
            for role in roles
        ]
