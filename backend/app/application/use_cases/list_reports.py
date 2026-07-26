"""List Reports Use Case."""

from __future__ import annotations

import math

from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.report_dto import ReportDTO
from app.domain.repositories.report_repository import IReportRepository
from app.domain.value_objects.filter_params import FilterParams


class ListReportsUseCase:
    """Orchestrates paginated and filtered listing of reports."""

    def __init__(self, report_repository: IReportRepository) -> None:
        self._report_repo = report_repository

    def execute(self, params: FilterParams) -> PaginatedResponse[ReportDTO]:
        """Fetch reports matching filter and pagination parameters."""
        items, total = self._report_repo.list(params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 0

        dtos = [ReportDTO.from_domain(r) for r in items]

        return PaginatedResponse[ReportDTO](
            items=dtos,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )
