"""Get Dashboard Use Case."""

from __future__ import annotations

from app.application.dto.dashboard_dto import DashboardDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dashboard_repository import IDashboardRepository


class GetDashboardUseCase:
    """Orchestrates retrieving a dashboard by ID."""

    def __init__(self, dashboard_repository: IDashboardRepository) -> None:
        self._dashboard_repo = dashboard_repository

    def execute(self, dashboard_id: str) -> DashboardDTO:
        """Retrieve a specific dashboard by ID.

        Raises
        ------
        EntityNotFoundError
            If dashboard with the given ID does not exist.
        """
        dashboard = self._dashboard_repo.get_by_id(dashboard_id)
        if dashboard is None:
            raise EntityNotFoundError("Dashboard", dashboard_id)

        return DashboardDTO.from_domain(dashboard)
