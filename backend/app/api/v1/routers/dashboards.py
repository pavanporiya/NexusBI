"""Dashboard Management REST API endpoints (v1 namespace)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_create_dashboard_use_case,
    get_current_user,
    get_delete_dashboard_use_case,
    get_get_dashboard_use_case,
    get_list_dashboards_use_case,
    get_update_dashboard_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.dashboard_dto import (
    CreateDashboardDTO,
    DashboardDTO,
    UpdateDashboardDTO,
)
from app.application.dto.error_dto import create_error_responses
from app.application.use_cases.create_dashboard import CreateDashboardUseCase
from app.application.use_cases.delete_dashboard import DeleteDashboardUseCase
from app.application.use_cases.get_dashboard import GetDashboardUseCase
from app.application.use_cases.list_dashboards import ListDashboardsUseCase
from app.application.use_cases.update_dashboard import UpdateDashboardUseCase
from app.domain.entities.user import User
from app.domain.value_objects.filter_params import FilterParams

router = APIRouter(prefix="/dashboards", tags=["Dashboard Management"])


@router.post(
    "",
    response_model=DashboardDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new dashboard",
    operation_id="dashboards_create",
    response_description="Created dashboard details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Creates a new BI dashboard referencing a dataset. Requires authentication "
        "and `dashboard:create` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:create"))],
)
def create_dashboard(
    dto: CreateDashboardDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[CreateDashboardUseCase, Depends(get_create_dashboard_use_case)],
) -> DashboardDTO:
    """Create a new dashboard."""
    return use_case.execute(dto, owner_id=current_user.id)


@router.get(
    "",
    response_model=PaginatedResponse[DashboardDTO],
    status_code=status.HTTP_200_OK,
    summary="List dashboards",
    operation_id="dashboards_list",
    response_description="Paginated list of dashboards matching filter criteria.",
    responses=create_error_responses(401, 403, 422, 500),
    description=(
        "Retrieves a paginated list of dashboards supporting filtering by owner, "
        "dataset, active status, public status, name, search, and sorting. "
        "Requires `dashboard:read` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:read"))],
)
def list_dashboards(
    use_case: Annotated[ListDashboardsUseCase, Depends(get_list_dashboards_use_case)],
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    name: Annotated[str | None, Query(description="Filter by name substring")] = None,
    owner_id: Annotated[
        str | None, Query(alias="owner", description="Filter by owner user ID")
    ] = None,
    dataset_id: Annotated[
        str | None, Query(alias="dataset", description="Filter by dataset ID")
    ] = None,
    is_active: Annotated[
        bool | None, Query(alias="active", description="Filter by active status")
    ] = None,
    is_public: Annotated[
        bool | None, Query(alias="public", description="Filter by public visibility")
    ] = None,
    created_at_from: Annotated[
        datetime | None, Query(description="Minimum creation timestamp")
    ] = None,
    created_at_to: Annotated[
        datetime | None, Query(description="Maximum creation timestamp")
    ] = None,
    updated_at_from: Annotated[
        datetime | None, Query(description="Minimum update timestamp")
    ] = None,
    updated_at_to: Annotated[
        datetime | None, Query(description="Maximum update timestamp")
    ] = None,
    search: Annotated[
        str | None, Query(description="Keyword search in name/description")
    ] = None,
    sort_by: Annotated[
        str, Query(description="Field to sort by ('name', 'created_at', 'updated_at')")
    ] = "created_at",
    sort_order: Annotated[
        str, Query(description="Sort order ('asc' or 'desc')")
    ] = "desc",
) -> PaginatedResponse[DashboardDTO]:
    """List dashboards with pagination, filtering, search, and sorting."""
    params = FilterParams(
        page=page,
        page_size=page_size,
        name=name,
        owner_id=owner_id,
        dataset_id=dataset_id,
        is_active=is_active,
        is_public=is_public,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        updated_at_from=updated_at_from,
        updated_at_to=updated_at_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return use_case.execute(params)


@router.get(
    "/{dashboard_id}",
    response_model=DashboardDTO,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard by ID",
    operation_id="dashboards_get_by_id",
    response_description="Dashboard details.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Retrieves details of a dashboard by ID. Requires `dashboard:read` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:read"))],
)
def get_dashboard(
    dashboard_id: str,
    use_case: Annotated[GetDashboardUseCase, Depends(get_get_dashboard_use_case)],
) -> DashboardDTO:
    """Retrieve details for a dashboard by ID."""
    return use_case.execute(dashboard_id)


@router.put(
    "/{dashboard_id}",
    response_model=DashboardDTO,
    status_code=status.HTTP_200_OK,
    summary="Replace dashboard",
    operation_id="dashboards_replace",
    response_description="Updated dashboard details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Replaces fields of an existing dashboard. "
        "Requires `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def replace_dashboard(
    dashboard_id: str,
    dto: UpdateDashboardDTO,
    use_case: Annotated[UpdateDashboardUseCase, Depends(get_update_dashboard_use_case)],
) -> DashboardDTO:
    """Replace an existing dashboard."""
    return use_case.execute(dashboard_id, dto)


@router.patch(
    "/{dashboard_id}",
    response_model=DashboardDTO,
    status_code=status.HTTP_200_OK,
    summary="Update dashboard",
    operation_id="dashboards_update",
    response_description="Updated dashboard details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Updates editable fields of a dashboard. "
        "Requires `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def update_dashboard(
    dashboard_id: str,
    dto: UpdateDashboardDTO,
    use_case: Annotated[UpdateDashboardUseCase, Depends(get_update_dashboard_use_case)],
) -> DashboardDTO:
    """Update an existing dashboard."""
    return use_case.execute(dashboard_id, dto)


@router.delete(
    "/{dashboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dashboard",
    operation_id="dashboards_delete",
    response_description="Dashboard successfully deleted.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Permanently deletes a dashboard. Requires `dashboard:delete` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:delete"))],
)
def delete_dashboard(
    dashboard_id: str,
    use_case: Annotated[DeleteDashboardUseCase, Depends(get_delete_dashboard_use_case)],
) -> None:
    """Delete a dashboard by ID."""
    use_case.execute(dashboard_id)
