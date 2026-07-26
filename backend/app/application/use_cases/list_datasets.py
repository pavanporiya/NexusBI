"""List Datasets Use Case."""

from __future__ import annotations

import math

from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.dataset_dto import DatasetDTO
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.value_objects.filter_params import FilterParams


class ListDatasetsUseCase:
    """Orchestrates paginated and filtered listing of datasets."""

    def __init__(self, dataset_repository: IDatasetRepository) -> None:
        self._dataset_repo = dataset_repository

    def execute(self, params: FilterParams) -> PaginatedResponse[DatasetDTO]:
        """Fetch datasets matching filter and pagination parameters."""
        items, total = self._dataset_repo.list(params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 0

        dtos = [DatasetDTO.from_domain(d) for d in items]

        return PaginatedResponse[DatasetDTO](
            items=dtos,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )
