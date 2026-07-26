"""List Widgets Use Case."""

from __future__ import annotations

from app.application.dto.widget_dto import WidgetDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dashboard_repository import IDashboardRepository
from app.domain.repositories.widget_repository import IWidgetRepository


class ListWidgetsUseCase:
    """Orchestrates retrieving all widgets contained inside a dashboard."""

    def __init__(
        self,
        widget_repository: IWidgetRepository,
        dashboard_repository: IDashboardRepository | None = None,
    ) -> None:
        self._widget_repo = widget_repository
        self._dashboard_repo = dashboard_repository

    def execute(self, dashboard_id: str) -> list[WidgetDTO]:
        """Fetch all widgets belonging to a dashboard.

        Parameters
        ----------
        dashboard_id : str
            Parent dashboard ID.

        Returns
        -------
        list[WidgetDTO]
            List of widget DTOs.
        """
        if self._dashboard_repo is not None:
            dashboard = self._dashboard_repo.get_by_id(dashboard_id)
            if dashboard is None:
                raise EntityNotFoundError("Dashboard", dashboard_id)

        widgets = self._widget_repo.list_by_dashboard_id(dashboard_id)
        return [WidgetDTO.from_domain(w) for w in widgets]
