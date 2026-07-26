"""Dashboard Widget Engine REST API endpoints (v1 namespace)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import (
    get_create_widget_use_case,
    get_delete_widget_use_case,
    get_get_widget_use_case,
    get_list_widgets_use_case,
    get_move_widget_use_case,
    get_resize_widget_use_case,
    get_toggle_visibility_use_case,
    get_update_widget_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.error_dto import create_error_responses
from app.application.dto.widget_dto import (
    CreateWidgetDTO,
    MoveWidgetDTO,
    ResizeWidgetDTO,
    ToggleVisibilityDTO,
    UpdateWidgetDTO,
    WidgetDTO,
)
from app.application.use_cases.create_widget import CreateWidgetUseCase
from app.application.use_cases.delete_widget import DeleteWidgetUseCase
from app.application.use_cases.get_widget import GetWidgetUseCase
from app.application.use_cases.list_widgets import ListWidgetsUseCase
from app.application.use_cases.move_widget import MoveWidgetUseCase
from app.application.use_cases.resize_widget import ResizeWidgetUseCase
from app.application.use_cases.toggle_visibility import ToggleVisibilityUseCase
from app.application.use_cases.update_widget import UpdateWidgetUseCase

router = APIRouter(tags=["Widget Management"])


@router.post(
    "/dashboards/{dashboard_id}/widgets",
    response_model=WidgetDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create widget inside dashboard",
    operation_id="widgets_create",
    response_description="Created widget details.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Creates a new visualization widget inside a target dashboard. "
        "Requires authentication and `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def create_widget(
    dashboard_id: str,
    dto: CreateWidgetDTO,
    use_case: Annotated[CreateWidgetUseCase, Depends(get_create_widget_use_case)],
) -> WidgetDTO:
    """Create a new widget in the specified dashboard."""
    return use_case.execute(dto, dashboard_id=dashboard_id)


@router.get(
    "/dashboards/{dashboard_id}/widgets",
    response_model=list[WidgetDTO],
    status_code=status.HTTP_200_OK,
    summary="List widgets in dashboard",
    operation_id="widgets_list_by_dashboard",
    response_description="List of widgets contained in dashboard.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Retrieves all widgets belonging to a specified dashboard. "
        "Requires `dashboard:read` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:read"))],
)
def list_widgets(
    dashboard_id: str,
    use_case: Annotated[ListWidgetsUseCase, Depends(get_list_widgets_use_case)],
) -> list[WidgetDTO]:
    """Retrieve all widgets inside a dashboard."""
    return use_case.execute(dashboard_id=dashboard_id)


@router.get(
    "/widgets/{widget_id}",
    response_model=WidgetDTO,
    status_code=status.HTTP_200_OK,
    summary="Get widget by ID",
    operation_id="widgets_get_by_id",
    response_description="Widget details.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Retrieves details of a widget by ID. Requires `dashboard:read` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:read"))],
)
def get_widget(
    widget_id: str,
    use_case: Annotated[GetWidgetUseCase, Depends(get_get_widget_use_case)],
) -> WidgetDTO:
    """Retrieve details for a widget by ID."""
    return use_case.execute(widget_id)


@router.put(
    "/widgets/{widget_id}",
    response_model=WidgetDTO,
    status_code=status.HTTP_200_OK,
    summary="Replace widget",
    operation_id="widgets_replace",
    response_description="Updated widget details.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Replaces fields of an existing widget. Requires `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def replace_widget(
    widget_id: str,
    dto: UpdateWidgetDTO,
    use_case: Annotated[UpdateWidgetUseCase, Depends(get_update_widget_use_case)],
) -> WidgetDTO:
    """Replace an existing widget."""
    return use_case.execute(widget_id, dto)


@router.patch(
    "/widgets/{widget_id}",
    response_model=WidgetDTO,
    status_code=status.HTTP_200_OK,
    summary="Update widget",
    operation_id="widgets_update",
    response_description="Updated widget details.",
    responses=create_error_responses(400, 401, 403, 404, 409, 422, 500),
    description=(
        "Updates editable fields of a widget. Requires `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def update_widget(
    widget_id: str,
    dto: UpdateWidgetDTO,
    use_case: Annotated[UpdateWidgetUseCase, Depends(get_update_widget_use_case)],
) -> WidgetDTO:
    """Update an existing widget."""
    return use_case.execute(widget_id, dto)


@router.delete(
    "/widgets/{widget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete widget",
    operation_id="widgets_delete",
    response_description="Widget successfully deleted.",
    responses=create_error_responses(401, 403, 404, 422, 500),
    description=(
        "Permanently deletes a widget. Requires `dashboard:delete` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:delete"))],
)
def delete_widget(
    widget_id: str,
    use_case: Annotated[DeleteWidgetUseCase, Depends(get_delete_widget_use_case)],
) -> None:
    """Delete a widget by ID."""
    use_case.execute(widget_id)


@router.patch(
    "/widgets/{widget_id}/move",
    response_model=WidgetDTO,
    status_code=status.HTTP_200_OK,
    summary="Move widget grid position",
    operation_id="widgets_move",
    response_description="Updated widget details with new position.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Updates the grid row and column position of a widget. "
        "Requires `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def move_widget(
    widget_id: str,
    dto: MoveWidgetDTO,
    use_case: Annotated[MoveWidgetUseCase, Depends(get_move_widget_use_case)],
) -> WidgetDTO:
    """Move a widget to a new row and column."""
    return use_case.execute(widget_id, dto)


@router.patch(
    "/widgets/{widget_id}/resize",
    response_model=WidgetDTO,
    status_code=status.HTTP_200_OK,
    summary="Resize widget grid dimensions",
    operation_id="widgets_resize",
    response_description="Updated widget details with new dimensions.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Updates the width and height grid dimensions of a widget. "
        "Requires `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def resize_widget(
    widget_id: str,
    dto: ResizeWidgetDTO,
    use_case: Annotated[ResizeWidgetUseCase, Depends(get_resize_widget_use_case)],
) -> WidgetDTO:
    """Resize a widget's grid width and height."""
    return use_case.execute(widget_id, dto)


@router.patch(
    "/widgets/{widget_id}/visibility",
    response_model=WidgetDTO,
    status_code=status.HTTP_200_OK,
    summary="Toggle or set widget visibility",
    operation_id="widgets_toggle_visibility",
    response_description="Updated widget details with new visibility status.",
    responses=create_error_responses(400, 401, 403, 404, 422, 500),
    description=(
        "Toggles or sets the visibility status flag of a widget. "
        "Requires `dashboard:update` permission."
    ),
    dependencies=[Depends(require_permission("dashboard:update"))],
)
def toggle_widget_visibility(
    widget_id: str,
    use_case: Annotated[
        ToggleVisibilityUseCase, Depends(get_toggle_visibility_use_case)
    ],
    dto: ToggleVisibilityDTO | None = None,
) -> WidgetDTO:
    """Toggle or update visibility of a widget."""
    return use_case.execute(widget_id, dto)
