"""Role Management REST API endpoints (v1 namespace).

Provides HTTP handlers for listing all RBAC roles, creating custom roles,
retrieving role details by ID, updating roles, and deleting roles.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import (
    get_create_role_use_case,
    get_delete_role_use_case,
    get_get_role_by_id_use_case,
    get_get_roles_use_case,
    get_update_role_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.error_dto import create_error_responses
from app.application.dto.role_dto import CreateRoleDTO, RoleDTO, UpdateRoleDTO
from app.application.use_cases import (
    CreateRoleUseCase,
    DeleteRoleUseCase,
    GetRoleByIdUseCase,
    GetRolesUseCase,
    UpdateRoleUseCase,
)

router = APIRouter(prefix="/roles", tags=["Role Management"])


@router.get(
    "",
    response_model=list[RoleDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all RBAC roles",
    operation_id="roles_get_all",
    response_description="List of system and custom roles with permissions.",
    responses=create_error_responses(401, 403, 500),
    description=(
        "Retrieves all RBAC roles defined in the system along with permissions. "
        "Requires authentication and the `roles:read` permission."
    ),
    dependencies=[Depends(require_permission("roles:read"))],
)
def get_roles(
    use_case: Annotated[GetRolesUseCase, Depends(get_get_roles_use_case)],
) -> list[RoleDTO]:
    """Retrieve all RBAC roles with assigned permissions."""
    return use_case.execute()


@router.post(
    "",
    response_model=RoleDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new RBAC role",
    operation_id="roles_create",
    response_description="Newly created RBAC role object.",
    responses=create_error_responses(400, 401, 403, 409, 422, 500),
    description=(
        "Creates a new custom RBAC role with specified name and permissions. "
        "Requires authentication and the `roles:create` permission."
    ),
    dependencies=[Depends(require_permission("roles:create"))],
)
def create_role(
    dto: CreateRoleDTO,
    use_case: Annotated[CreateRoleUseCase, Depends(get_create_role_use_case)],
) -> RoleDTO:
    """Create a new custom RBAC role with assigned permissions."""
    return use_case.execute(dto)


@router.get(
    "/{role_id}",
    response_model=RoleDTO,
    status_code=status.HTTP_200_OK,
    summary="Get role details by ID",
    operation_id="roles_get_by_id",
    response_description="Target RBAC role details and permissions.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Retrieves detailed definition and permissions for a specific RBAC role. "
        "Requires authentication and the `roles:read` permission."
    ),
    dependencies=[Depends(require_permission("roles:read"))],
)
def get_role_by_id(
    role_id: str,
    use_case: Annotated[GetRoleByIdUseCase, Depends(get_get_role_by_id_use_case)],
) -> RoleDTO:
    """Retrieve details for a specific RBAC role by identifier."""
    return use_case.execute(role_id)


@router.patch(
    "/{role_id}",
    response_model=RoleDTO,
    status_code=status.HTTP_200_OK,
    summary="Update an existing RBAC role",
    operation_id="roles_update",
    response_description="Updated RBAC role definition.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Updates name, description, or permissions for a specific RBAC role. "
        "Requires authentication and the `roles:update` permission."
    ),
    dependencies=[Depends(require_permission("roles:update"))],
)
def update_role(
    role_id: str,
    dto: UpdateRoleDTO,
    use_case: Annotated[UpdateRoleUseCase, Depends(get_update_role_use_case)],
) -> RoleDTO:
    """Update role metadata or assigned permissions for a specific role ID."""
    return use_case.execute(role_id, dto)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an RBAC role",
    operation_id="roles_delete",
    response_description="Role successfully deleted.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Deletes a custom RBAC role by identifier. "
        "System default roles cannot be deleted. "
        "Requires authentication and the `roles:delete` permission."
    ),
    dependencies=[Depends(require_permission("roles:delete"))],
)
def delete_role(
    role_id: str,
    use_case: Annotated[DeleteRoleUseCase, Depends(get_delete_role_use_case)],
) -> None:
    """Delete a custom RBAC role by identifier.

    Default system roles cannot be deleted.
    """
    use_case.execute(role_id)
