"""Create Widget Use Case."""

from __future__ import annotations

import uuid

from app.application.dto.widget_dto import CreateWidgetDTO, WidgetDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.widget import Widget
from app.domain.repositories.dashboard_repository import IDashboardRepository
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.repositories.widget_repository import IWidgetRepository


class CreateWidgetUseCase:
    """Orchestrates creating a new widget inside a dashboard."""

    def __init__(
        self,
        widget_repository: IWidgetRepository,
        dashboard_repository: IDashboardRepository | None = None,
        dataset_repository: IDatasetRepository | None = None,
    ) -> None:
        self._widget_repo = widget_repository
        self._dashboard_repo = dashboard_repository
        self._dataset_repo = dataset_repository

    def execute(
        self, dto: CreateWidgetDTO, dashboard_id: str | None = None
    ) -> WidgetDTO:
        """Create and persist a new Widget domain entity.

        Parameters
        ----------
        dto : CreateWidgetDTO
            Widget creation request payload.
        dashboard_id : str | None
            Parent dashboard ID (overrides dto.dashboard_id if provided).

        Returns
        -------
        WidgetDTO
            The created Widget DTO.
        """
        target_dashboard_id = dashboard_id or dto.dashboard_id or ""
        if not target_dashboard_id or not target_dashboard_id.strip():
            raise EntityNotFoundError("Dashboard", target_dashboard_id)

        # 1. Validate dashboard exists
        if self._dashboard_repo is not None:
            dashboard = self._dashboard_repo.get_by_id(target_dashboard_id)
            if dashboard is None:
                raise EntityNotFoundError("Dashboard", target_dashboard_id)

        # 2. Validate dataset exists
        if self._dataset_repo is not None:
            dataset = self._dataset_repo.get_by_id(dto.dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dto.dataset_id)

        # 3. Check duplicate widget inside dashboard
        existing = self._widget_repo.get_by_dashboard_and_title(
            target_dashboard_id, dto.title.strip()
        )
        if existing is not None:
            raise DuplicateEntityError(
                "Widget", f"Dashboard '{target_dashboard_id}' with title '{dto.title}'"
            )

        # 4. Construct and save widget aggregate
        widget_id = str(uuid.uuid4())
        widget = Widget(
            id=widget_id,
            dashboard_id=target_dashboard_id,
            dataset_id=dto.dataset_id,
            title=dto.title,
            widget_type=dto.widget_type,
            position=dto.position.model_dump(),
            size=dto.size.model_dump(),
            configuration=dto.configuration,
            refresh_interval=dto.refresh_interval,
            is_visible=dto.is_visible,
        )

        saved = self._widget_repo.save(widget)
        return WidgetDTO.from_domain(saved)
