"""Organization Management REST API endpoints (v1 namespace)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_create_organization_use_case,
    get_delete_organization_use_case,
    get_get_organization_use_case,
    get_list_organizations_use_case,
    get_update_organization_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.error_dto import create_error_responses
from app.application.dto.organization_dto import (
    CreateOrganizationDTO,
    OrganizationDTO,
    UpdateOrganizationDTO,
)
from app.application.use_cases.create_organization import CreateOrganizationUseCase
from app.application.use_cases.delete_organization import DeleteOrganizationUseCase
from app.application.use_cases.get_organization import GetOrganizationUseCase
from app.application.use_cases.list_organizations import ListOrganizationsUseCase
from app.application.use_cases.update_organization import UpdateOrganizationUseCase

router = APIRouter(prefix="/organizations", tags=["Organization Management"])


@router.post(
    "",
    response_model=OrganizationDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new organization",
    operation_id="organizations_create",
    response_description="Created organization details.",
    responses=create_error_responses(400, 401, 403, 409, 422, 500),
    description=(
        "Creates a new enterprise organization. "
        "Requires `organizations:create` permission."
    ),
    dependencies=[Depends(require_permission("organizations:create"))],
)
def create_organization(
    dto: CreateOrganizationDTO,
    use_case: Annotated[
        CreateOrganizationUseCase, Depends(get_create_organization_use_case)
    ],
) -> OrganizationDTO:
    """Create a new organization."""
    return use_case.execute(dto)


@router.get(
    "",
    response_model=PaginatedResponse[OrganizationDTO],
    status_code=status.HTTP_200_OK,
    summary="List organizations",
    operation_id="organizations_list",
    response_description="Paginated list of organizations.",
    responses=create_error_responses(401, 403, 422, 500),
    description=(
        "Retrieves a paginated list of enterprise organizations. "
        "Requires `organizations:read` permission."
    ),
    dependencies=[Depends(require_permission("organizations:read"))],
)
def list_organizations(
    use_case: Annotated[
        ListOrganizationsUseCase, Depends(get_list_organizations_use_case)
    ],
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginatedResponse[OrganizationDTO]:
    """List organizations."""
    return use_case.execute(page=page, page_size=page_size)


@router.get(
    "/{organization_id}",
    response_model=OrganizationDTO,
    status_code=status.HTTP_200_OK,
    summary="Get organization by ID",
    operation_id="organizations_get",
    response_description="Organization details.",
    responses=create_error_responses(401, 403, 404, 500),
    description=(
        "Retrieves an organization by its unique ID. "
        "Requires `organizations:read` permission."
    ),
    dependencies=[Depends(require_permission("organizations:read"))],
)
def get_organization(
    organization_id: str,
    use_case: Annotated[GetOrganizationUseCase, Depends(get_get_organization_use_case)],
) -> OrganizationDTO:
    """Get organization by ID."""
    return use_case.execute(organization_id)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationDTO,
    status_code=status.HTTP_200_OK,
    summary="Update organization",
    operation_id="organizations_update",
    response_description="Updated organization details.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Updates an existing organization. Requires `organizations:update` permission."
    ),
    dependencies=[Depends(require_permission("organizations:update"))],
)
def update_organization(
    organization_id: str,
    dto: UpdateOrganizationDTO,
    use_case: Annotated[
        UpdateOrganizationUseCase, Depends(get_update_organization_use_case)
    ],
) -> OrganizationDTO:
    """Update organization."""
    return use_case.execute(organization_id, dto)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization",
    operation_id="organizations_delete",
    responses=create_error_responses(401, 403, 404, 500),
    description=(
        "Permanently deletes an organization. "
        "Requires `organizations:delete` permission."
    ),
    dependencies=[Depends(require_permission("organizations:delete"))],
)
def delete_organization(
    organization_id: str,
    use_case: Annotated[
        DeleteOrganizationUseCase, Depends(get_delete_organization_use_case)
    ],
) -> None:
    """Delete organization."""
    use_case.execute(organization_id)
