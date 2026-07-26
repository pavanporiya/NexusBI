"""List Dashboards Use Case."""

from __future__ import annotations

import math

from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.dashboard_dto import DashboardDTO
from app.domain.repositories.dashboard_repository import IDashboardRepository
from app.domain.value_objects.filter_params import FilterParams


class ListDashboardsUseCase:
    """Orchestrates paginated and filtered listing of dashboards."""

    def __init__(self, dashboard_repository: IDashboardRepository) -> None:
        self._dashboard_repo = dashboard_repository

    def execute(self, params: FilterParams) -> PaginatedResponse[DashboardDTO]:
        """Fetch dashboards matching filter and pagination parameters."""
        items, total = self._dashboard_repo.list(params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 0

        dtos = [DashboardDTO.from_domain(d) for d in items]

        return PaginatedResponse[DashboardDTO](
            items=dtos,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )
