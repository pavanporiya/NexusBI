"""Delete Dashboard Use Case."""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dashboard_repository import IDashboardRepository


class DeleteDashboardUseCase:
    """Orchestrates deleting a dashboard."""

    def __init__(self, dashboard_repository: IDashboardRepository) -> None:
        self._dashboard_repo = dashboard_repository

    def execute(self, dashboard_id: str) -> None:
        """Delete a dashboard by ID.

        Raises
        ------
        EntityNotFoundError
            If dashboard with dashboard_id does not exist.
        """
        deleted = self._dashboard_repo.delete(dashboard_id)
        if not deleted:
            raise EntityNotFoundError("Dashboard", dashboard_id)
