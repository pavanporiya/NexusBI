"""Dataset Management REST API endpoints (v1 namespace)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_create_dataset_use_case,
    get_current_user,
    get_delete_dataset_use_case,
    get_get_dataset_use_case,
    get_list_datasets_use_case,
    get_update_dataset_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.dataset_dto import (
    CreateDatasetDTO,
    DatasetDTO,
    UpdateDatasetDTO,
)
from app.application.dto.error_dto import create_error_responses
from app.application.use_cases.create_dataset import CreateDatasetUseCase
from app.application.use_cases.delete_dataset import DeleteDatasetUseCase
from app.application.use_cases.get_dataset import GetDatasetUseCase
from app.application.use_cases.list_datasets import ListDatasetsUseCase
from app.application.use_cases.update_dataset import UpdateDatasetUseCase
from app.domain.entities.user import User
from app.domain.value_objects.filter_params import FilterParams

router = APIRouter(prefix="/datasets", tags=["Dataset Management"])


@router.post(
    "",
    response_model=DatasetDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new dataset",
    operation_id="datasets_create",
    response_description="Created dataset details.",
    responses=create_error_responses(400, 401, 403, 422, 500),
    description=(
        "Creates a new dataset. Requires authentication "
        "and `datasets:create` permission."
    ),
    dependencies=[Depends(require_permission("datasets:create"))],
)
def create_dataset(
    dto: CreateDatasetDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[CreateDatasetUseCase, Depends(get_create_dataset_use_case)],
) -> DatasetDTO:
    """Create a new dataset."""
    return use_case.execute(dto, owner_id=current_user.id)


@router.get(
    "",
    response_model=PaginatedResponse[DatasetDTO],
    status_code=status.HTTP_200_OK,
    summary="List datasets",
    operation_id="datasets_list",
    response_description="Paginated list of datasets matching filter criteria.",
    responses=create_error_responses(401, 403, 422, 500),
    description=(
        "Retrieves a paginated list of datasets supporting filtering by "
        "name, owner, active status, timestamps, search, and sorting. "
        "Requires `datasets:read` permission."
    ),
    dependencies=[Depends(require_permission("datasets:read"))],
)
def list_datasets(
    use_case: Annotated[ListDatasetsUseCase, Depends(get_list_datasets_use_case)],
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    name: Annotated[str | None, Query(description="Filter by name substring")] = None,
    owner_id: Annotated[
        str | None, Query(description="Filter by owner user ID")
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
    is_active: Annotated[
        bool | None, Query(description="Filter by active status")
    ] = None,
    search: Annotated[
        str | None, Query(description="Keyword search in name/description")
    ] = None,
    sort_by: Annotated[str, Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[
        str, Query(description="Sort order ('asc' or 'desc')")
    ] = "desc",
) -> PaginatedResponse[DatasetDTO]:
    """List datasets with pagination, filtering, search, and sorting."""
    params = FilterParams(
        page=page,
        page_size=page_size,
        name=name,
        owner_id=owner_id,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        updated_at_from=updated_at_from,
        updated_at_to=updated_at_to,
        is_active=is_active,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return use_case.execute(params)


@router.get(
    "/{dataset_id}",
    response_model=DatasetDTO,
    status_code=status.HTTP_200_OK,
    summary="Get dataset by ID",
    operation_id="datasets_get_by_id",
    response_description="Dataset details.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Retrieves details of a dataset by ID. Requires `datasets:read` permission."
    ),
    dependencies=[Depends(require_permission("datasets:read"))],
)
def get_dataset(
    dataset_id: str,
    use_case: Annotated[GetDatasetUseCase, Depends(get_get_dataset_use_case)],
) -> DatasetDTO:
    """Retrieve details for a dataset by ID."""
    return use_case.execute(dataset_id)


@router.put(
    "/{dataset_id}",
    response_model=DatasetDTO,
    status_code=status.HTTP_200_OK,
    summary="Replace dataset",
    operation_id="datasets_replace",
    response_description="Replaced dataset details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Replaces editable fields of a dataset (full update). "
        "Requires `datasets:update` permission."
    ),
    dependencies=[Depends(require_permission("datasets:update"))],
)
def replace_dataset(
    dataset_id: str,
    dto: UpdateDatasetDTO,
    use_case: Annotated[UpdateDatasetUseCase, Depends(get_update_dataset_use_case)],
) -> DatasetDTO:
    """Replace (full update) an existing dataset."""
    return use_case.execute(dataset_id, dto)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetDTO,
    status_code=status.HTTP_200_OK,
    summary="Partially update dataset",
    operation_id="datasets_update",
    response_description="Updated dataset details.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Partially updates editable fields of a dataset. "
        "Requires `datasets:update` permission."
    ),
    dependencies=[Depends(require_permission("datasets:update"))],
)
def update_dataset(
    dataset_id: str,
    dto: UpdateDatasetDTO,
    use_case: Annotated[UpdateDatasetUseCase, Depends(get_update_dataset_use_case)],
) -> DatasetDTO:
    """Partially update an existing dataset."""
    return use_case.execute(dataset_id, dto)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dataset",
    operation_id="datasets_delete",
    response_description="Dataset successfully deleted.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Permanently deletes a dataset. Requires `datasets:delete` permission."
    ),
    dependencies=[Depends(require_permission("datasets:delete"))],
)
def delete_dataset(
    dataset_id: str,
    use_case: Annotated[DeleteDatasetUseCase, Depends(get_delete_dataset_use_case)],
) -> None:
    """Delete a dataset by ID."""
    use_case.execute(dataset_id)
