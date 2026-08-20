"""Create role use case.

Orchestrates creation of new RBAC roles and permission assignments.
"""

from __future__ import annotations

import uuid

from app.application.dto.role_dto import CreateRoleDTO, PermissionDTO, RoleDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.role import Role
from app.domain.repositories.role_repository import IRoleRepository


class CreateRoleUseCase:
    """Orchestrates creating a new RBAC role."""

    def __init__(self, role_repository: IRoleRepository) -> None:
        self._role_repo = role_repository

    def execute(self, dto: CreateRoleDTO) -> RoleDTO:
        """Create a new system role.

        Parameters
        ----------
        dto : CreateRoleDTO
            Role creation request data containing name, description, and permission IDs.

        Returns
        -------
        RoleDTO
            The created role data transfer object.

        Raises
        ------
        DuplicateEntityError
            If a role with the given name already exists.
        EntityNotFoundError
            If any assigned permission ID does not exist.
        """
        existing = self._role_repo.get_by_name(dto.name)
        if existing is not None:
            raise DuplicateEntityError("Role", dto.name)

        permissions = []
        if dto.permission_ids:
            permissions = self._role_repo.get_permissions_by_ids(dto.permission_ids)
            found_keys = {p.id for p in permissions} | {
                p.qualified_name for p in permissions
            }
            for pid in dto.permission_ids:
                if pid not in found_keys:
                    raise EntityNotFoundError("Permission", pid)

        role_id = str(uuid.uuid4())
        new_role = Role(
            id=role_id,
            name=dto.name,
            description=dto.description,
            permissions=permissions,
        )

        saved_role = self._role_repo.save(new_role)

        return RoleDTO(
            id=saved_role.id,
            name=saved_role.name,
            description=saved_role.description,
            permissions=[
                PermissionDTO(
                    id=perm.id,
                    resource=perm.resource,
                    action=perm.action,
                    description=perm.description,
                )
                for perm in saved_role.permissions
            ],
        )
