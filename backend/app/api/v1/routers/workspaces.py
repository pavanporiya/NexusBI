"""Workspace & Membership Management REST API endpoints (v1 namespace)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_add_member_use_case,
    get_create_workspace_use_case,
    get_delete_workspace_use_case,
    get_get_workspace_use_case,
    get_list_members_use_case,
    get_list_workspaces_use_case,
    get_remove_member_use_case,
    get_update_member_role_use_case,
    get_update_workspace_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.error_dto import create_error_responses
from app.application.dto.membership_dto import (
    AddMemberDTO,
    MembershipDTO,
    UpdateMemberRoleDTO,
)
from app.application.dto.workspace_dto import (
    CreateWorkspaceDTO,
    UpdateWorkspaceDTO,
    WorkspaceDTO,
)
from app.application.use_cases.add_member import AddMemberUseCase
from app.application.use_cases.create_workspace import CreateWorkspaceUseCase
from app.application.use_cases.delete_workspace import DeleteWorkspaceUseCase
from app.application.use_cases.get_workspace import GetWorkspaceUseCase
from app.application.use_cases.list_members import ListMembersUseCase
from app.application.use_cases.list_workspaces import ListWorkspacesUseCase
from app.application.use_cases.remove_member import RemoveMemberUseCase
from app.application.use_cases.update_member_role import UpdateMemberRoleUseCase
from app.application.use_cases.update_workspace import UpdateWorkspaceUseCase

router = APIRouter(prefix="/workspaces", tags=["Workspace Management"])


# ---------------------------------------------------------------------------
# Workspace Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=WorkspaceDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new workspace",
    operation_id="workspaces_create",
    response_description="Created workspace details.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Creates a new workspace within an organization. "
        "Requires `workspaces:create` permission."
    ),
    dependencies=[Depends(require_permission("workspaces:create"))],
)
def create_workspace(
    dto: CreateWorkspaceDTO,
    use_case: Annotated[CreateWorkspaceUseCase, Depends(get_create_workspace_use_case)],
) -> WorkspaceDTO:
    """Create a new workspace."""
    return use_case.execute(dto)


@router.get(
    "",
    response_model=PaginatedResponse[WorkspaceDTO],
    status_code=status.HTTP_200_OK,
    summary="List workspaces",
    operation_id="workspaces_list",
    response_description="Paginated list of workspaces.",
    responses=create_error_responses(401, 403, 422, 500),
    description=(
        "Retrieves a paginated list of workspaces. "
        "Requires `workspaces:read` permission."
    ),
    dependencies=[Depends(require_permission("workspaces:read"))],
)
def list_workspaces(
    use_case: Annotated[ListWorkspacesUseCase, Depends(get_list_workspaces_use_case)],
    organization_id: Annotated[
        str | None, Query(alias="organization", description="Filter by Organization ID")
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginatedResponse[WorkspaceDTO]:
    """List workspaces."""
    return use_case.execute(
        organization_id=organization_id, page=page, page_size=page_size
    )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDTO,
    status_code=status.HTTP_200_OK,
    summary="Get workspace by ID",
    operation_id="workspaces_get",
    response_description="Workspace details.",
    responses=create_error_responses(401, 403, 404, 500),
    description=(
        "Retrieves a workspace by its unique ID. Requires `workspaces:read` permission."
    ),
    dependencies=[Depends(require_permission("workspaces:read"))],
)
def get_workspace(
    workspace_id: str,
    use_case: Annotated[GetWorkspaceUseCase, Depends(get_get_workspace_use_case)],
) -> WorkspaceDTO:
    """Get workspace by ID."""
    return use_case.execute(workspace_id)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceDTO,
    status_code=status.HTTP_200_OK,
    summary="Update workspace",
    operation_id="workspaces_update",
    response_description="Updated workspace details.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Updates an existing workspace. Requires `workspaces:update` permission."
    ),
    dependencies=[Depends(require_permission("workspaces:update"))],
)
def update_workspace(
    workspace_id: str,
    dto: UpdateWorkspaceDTO,
    use_case: Annotated[UpdateWorkspaceUseCase, Depends(get_update_workspace_use_case)],
) -> WorkspaceDTO:
    """Update workspace."""
    return use_case.execute(workspace_id, dto)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workspace",
    operation_id="workspaces_delete",
    responses=create_error_responses(401, 403, 404, 500),
    description=(
        "Permanently deletes a workspace. Requires `workspaces:delete` permission."
    ),
    dependencies=[Depends(require_permission("workspaces:delete"))],
)
def delete_workspace(
    workspace_id: str,
    use_case: Annotated[DeleteWorkspaceUseCase, Depends(get_delete_workspace_use_case)],
) -> None:
    """Delete workspace."""
    use_case.execute(workspace_id)


# ---------------------------------------------------------------------------
# Membership Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{workspace_id}/members",
    response_model=MembershipDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add member to workspace",
    operation_id="memberships_add",
    response_description="Added membership details.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Adds a user as a member to a workspace. "
        "Requires `memberships:create` permission."
    ),
    dependencies=[Depends(require_permission("memberships:create"))],
)
def add_member(
    workspace_id: str,
    dto: AddMemberDTO,
    use_case: Annotated[AddMemberUseCase, Depends(get_add_member_use_case)],
) -> MembershipDTO:
    """Add member to workspace."""
    return use_case.execute(workspace_id, dto)


@router.get(
    "/{workspace_id}/members",
    response_model=PaginatedResponse[MembershipDTO],
    status_code=status.HTTP_200_OK,
    summary="List workspace members",
    operation_id="memberships_list",
    response_description="Paginated list of workspace members.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Retrieves a paginated list of workspace members. "
        "Requires `memberships:read` permission."
    ),
    dependencies=[Depends(require_permission("memberships:read"))],
)
def list_members(
    workspace_id: str,
    use_case: Annotated[ListMembersUseCase, Depends(get_list_members_use_case)],
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginatedResponse[MembershipDTO]:
    """List workspace members."""
    return use_case.execute(workspace_id, page=page, page_size=page_size)


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=MembershipDTO,
    status_code=status.HTTP_200_OK,
    summary="Update member role in workspace",
    operation_id="memberships_update",
    response_description="Updated membership details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Updates a member's role in a workspace. "
        "Requires `memberships:update` permission."
    ),
    dependencies=[Depends(require_permission("memberships:update"))],
)
def update_member_role(
    workspace_id: str,
    user_id: str,
    dto: UpdateMemberRoleDTO,
    use_case: Annotated[
        UpdateMemberRoleUseCase, Depends(get_update_member_role_use_case)
    ],
) -> MembershipDTO:
    """Update member role in workspace."""
    return use_case.execute(workspace_id, user_id, dto)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from workspace",
    operation_id="memberships_remove",
    responses=create_error_responses(401, 403, 404, 500),
    description=(
        "Removes a member from a workspace. Requires `memberships:delete` permission."
    ),
    dependencies=[Depends(require_permission("memberships:delete"))],
)
def remove_member(
    workspace_id: str,
    user_id: str,
    use_case: Annotated[RemoveMemberUseCase, Depends(get_remove_member_use_case)],
) -> None:
    """Remove member from workspace."""
    use_case.execute(workspace_id, user_id)
