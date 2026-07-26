"""Create Dashboard Use Case."""

from __future__ import annotations

import uuid

from app.application.dto.dashboard_dto import CreateDashboardDTO, DashboardDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.dashboard import Dashboard
from app.domain.repositories.dashboard_repository import IDashboardRepository
from app.domain.repositories.dataset_repository import IDatasetRepository


class CreateDashboardUseCase:
    """Orchestrates creating a new dashboard."""

    def __init__(
        self,
        dashboard_repository: IDashboardRepository,
        dataset_repository: IDatasetRepository | None = None,
    ) -> None:
        self._dashboard_repo = dashboard_repository
        self._dataset_repo = dataset_repository

    def execute(self, dto: CreateDashboardDTO, owner_id: str) -> DashboardDTO:
        """Create and persist a new Dashboard entity.

        Parameters
        ----------
        dto : CreateDashboardDTO
            Request data payload.
        owner_id : str
            User ID of the creating user.

        Returns
        -------
        DashboardDTO
            The created dashboard DTO.
        """
        if self._dataset_repo is not None:
            dataset = self._dataset_repo.get_by_id(dto.dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dto.dataset_id)

        dashboard_id = str(uuid.uuid4())
        dashboard = Dashboard(
            id=dashboard_id,
            name=dto.name,
            owner_id=owner_id,
            dataset_id=dto.dataset_id,
            description=dto.description,
            layout_json=dto.layout_json,
            is_public=dto.is_public,
            is_active=dto.is_active,
        )
        saved = self._dashboard_repo.save(dashboard)
        return DashboardDTO.from_domain(saved)
