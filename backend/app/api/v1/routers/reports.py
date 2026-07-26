"""Report Management REST API endpoints (v1 namespace)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_create_report_use_case,
    get_current_user,
    get_delete_report_use_case,
    get_get_report_use_case,
    get_list_reports_use_case,
    get_update_report_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.error_dto import create_error_responses
from app.application.dto.report_dto import (
    CreateReportDTO,
    ReportDTO,
    UpdateReportDTO,
)
from app.application.use_cases.create_report import CreateReportUseCase
from app.application.use_cases.delete_report import DeleteReportUseCase
from app.application.use_cases.get_report import GetReportUseCase
from app.application.use_cases.list_reports import ListReportsUseCase
from app.application.use_cases.update_report import UpdateReportUseCase
from app.domain.entities.user import User
from app.domain.value_objects.filter_params import FilterParams

router = APIRouter(prefix="/reports", tags=["Report Management"])


@router.post(
    "",
    response_model=ReportDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new report",
    operation_id="reports_create",
    response_description="Created report details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Creates a new analytical report referencing a dataset. "
        "Requires authentication and `reports:create` permission."
    ),
    dependencies=[Depends(require_permission("reports:create"))],
)
def create_report(
    dto: CreateReportDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[CreateReportUseCase, Depends(get_create_report_use_case)],
) -> ReportDTO:
    """Create a new report."""
    return use_case.execute(dto, owner_id=current_user.id)


@router.get(
    "",
    response_model=PaginatedResponse[ReportDTO],
    status_code=status.HTTP_200_OK,
    summary="List reports",
    operation_id="reports_list",
    response_description="Paginated list of reports matching filter criteria.",
    responses=create_error_responses(401, 403, 422, 500),
    description=(
        "Retrieves a paginated list of reports supporting filtering by dataset, owner, "
        "report_type, active status, name, search, and sorting. "
        "Requires `reports:read` permission."
    ),
    dependencies=[Depends(require_permission("reports:read"))],
)
def list_reports(
    use_case: Annotated[ListReportsUseCase, Depends(get_list_reports_use_case)],
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    name: Annotated[str | None, Query(description="Filter by name substring")] = None,
    owner_id: Annotated[
        str | None, Query(alias="owner", description="Filter by owner user ID")
    ] = None,
    dataset_id: Annotated[
        str | None, Query(alias="dataset", description="Filter by dataset ID")
    ] = None,
    report_type: Annotated[
        str | None, Query(description="Filter by report_type")
    ] = None,
    is_active: Annotated[
        bool | None, Query(alias="active", description="Filter by active status")
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
        str | None, Query(description="Keyword search in name/description/type/format")
    ] = None,
    sort_by: Annotated[
        str, Query(description="Field to sort by ('name', 'created_at', 'updated_at')")
    ] = "created_at",
    sort_order: Annotated[
        str, Query(description="Sort order ('asc' or 'desc')")
    ] = "desc",
) -> PaginatedResponse[ReportDTO]:
    """List reports with pagination, filtering, search, and sorting."""
    params = FilterParams(
        page=page,
        page_size=page_size,
        name=name,
        owner_id=owner_id,
        dataset_id=dataset_id,
        report_type=report_type,
        is_active=is_active,
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
    "/{report_id}",
    response_model=ReportDTO,
    status_code=status.HTTP_200_OK,
    summary="Get report by ID",
    operation_id="reports_get_by_id",
    response_description="Report details.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Retrieves details of a report by ID. Requires `reports:read` permission."
    ),
    dependencies=[Depends(require_permission("reports:read"))],
)
def get_report(
    report_id: str,
    use_case: Annotated[GetReportUseCase, Depends(get_get_report_use_case)],
) -> ReportDTO:
    """Retrieve details for a report by ID."""
    return use_case.execute(report_id)


@router.put(
    "/{report_id}",
    response_model=ReportDTO,
    status_code=status.HTTP_200_OK,
    summary="Replace report",
    operation_id="reports_replace",
    response_description="Updated report details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Replaces fields of an existing report. Requires `reports:update` permission."
    ),
    dependencies=[Depends(require_permission("reports:update"))],
)
def replace_report(
    report_id: str,
    dto: UpdateReportDTO,
    use_case: Annotated[UpdateReportUseCase, Depends(get_update_report_use_case)],
) -> ReportDTO:
    """Replace an existing report."""
    return use_case.execute(report_id, dto)


@router.patch(
    "/{report_id}",
    response_model=ReportDTO,
    status_code=status.HTTP_200_OK,
    summary="Update report",
    operation_id="reports_update",
    response_description="Updated report details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Updates editable fields of a report. Requires `reports:update` permission."
    ),
    dependencies=[Depends(require_permission("reports:update"))],
)
def update_report(
    report_id: str,
    dto: UpdateReportDTO,
    use_case: Annotated[UpdateReportUseCase, Depends(get_update_report_use_case)],
) -> ReportDTO:
    """Update an existing report."""
    return use_case.execute(report_id, dto)


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete report",
    operation_id="reports_delete",
    response_description="Report successfully deleted.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=("Permanently deletes a report. Requires `reports:delete` permission."),
    dependencies=[Depends(require_permission("reports:delete"))],
)
def delete_report(
    report_id: str,
    use_case: Annotated[DeleteReportUseCase, Depends(get_delete_report_use_case)],
) -> None:
    """Delete a report by ID."""
    use_case.execute(report_id)
