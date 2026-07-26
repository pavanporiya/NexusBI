"""Update Dashboard Use Case."""

from __future__ import annotations

from app.application.dto.dashboard_dto import DashboardDTO, UpdateDashboardDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dashboard_repository import IDashboardRepository
from app.domain.repositories.dataset_repository import IDatasetRepository


class UpdateDashboardUseCase:
    """Orchestrates updating an existing dashboard."""

    def __init__(
        self,
        dashboard_repository: IDashboardRepository,
        dataset_repository: IDatasetRepository | None = None,
    ) -> None:
        self._dashboard_repo = dashboard_repository
        self._dataset_repo = dataset_repository

    def execute(self, dashboard_id: str, dto: UpdateDashboardDTO) -> DashboardDTO:
        """Update dashboard attributes.

        Raises
        ------
        EntityNotFoundError
            If dashboard or dataset does not exist.
        """
        dashboard = self._dashboard_repo.get_by_id(dashboard_id)
        if dashboard is None:
            raise EntityNotFoundError("Dashboard", dashboard_id)

        if dto.dataset_id is not None and self._dataset_repo is not None:
            dataset = self._dataset_repo.get_by_id(dto.dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dto.dataset_id)

        dashboard.update(
            name=dto.name,
            description=dto.description,
            dataset_id=dto.dataset_id,
            layout_json=dto.layout_json,
            is_public=dto.is_public,
            is_active=dto.is_active,
        )
        saved = self._dashboard_repo.save(dashboard)

        return DashboardDTO.from_domain(saved)
