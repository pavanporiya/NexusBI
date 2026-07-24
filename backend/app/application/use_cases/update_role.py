"""Update role use case.

Orchestrates updating role metadata and permission assignments.
"""

from __future__ import annotations

from app.application.dto.role_dto import PermissionDTO, RoleDTO, UpdateRoleDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.repositories.role_repository import IRoleRepository


class UpdateRoleUseCase:
    """Orchestrates updating an existing RBAC role."""

    def __init__(self, role_repository: IRoleRepository) -> None:
        self._role_repo = role_repository

    def execute(self, role_id: str, dto: UpdateRoleDTO) -> RoleDTO:
        """Update role details and permissions for the specified role ID.

        Parameters
        ----------
        role_id : str
            Unique identifier of the role to update.
        dto : UpdateRoleDTO
            Patch request data containing optional name, description, or permission IDs.

        Returns
        -------
        RoleDTO
            The updated role data transfer object.

        Raises
        ------
        EntityNotFoundError
            If the role or any specified permission ID does not exist.
        DuplicateEntityError
            If updating name to an already existing role name.
        """
        role = self._role_repo.get_by_id(role_id)
        if role is None:
            raise EntityNotFoundError("Role", role_id)

        if dto.name is not None and dto.name != role.name:
            existing = self._role_repo.get_by_name(dto.name)
            if existing is not None and existing.id != role_id:
                raise DuplicateEntityError("Role", dto.name)
            role.name = dto.name

        if dto.description is not None:
            role.description = dto.description

        if dto.permission_ids is not None:
            permissions = self._role_repo.get_permissions_by_ids(dto.permission_ids)
            found_keys = {p.id for p in permissions} | {
                p.qualified_name for p in permissions
            }
            for pid in dto.permission_ids:
                if pid not in found_keys:
                    raise EntityNotFoundError("Permission", pid)
            role.permissions = permissions

        saved_role = self._role_repo.save(role)

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
