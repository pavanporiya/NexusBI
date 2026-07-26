"""Get Dataset Use Case."""

from __future__ import annotations

from app.application.dto.dataset_dto import DatasetDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dataset_repository import IDatasetRepository


class GetDatasetUseCase:
    """Orchestrates loading a dataset by ID."""

    def __init__(self, dataset_repository: IDatasetRepository) -> None:
        self._dataset_repo = dataset_repository

    def execute(self, dataset_id: str) -> DatasetDTO:
        """Retrieve a specific dataset by ID.

        Raises
        ------
        EntityNotFoundError
            If dataset with dataset_id does not exist.
        """
        dataset = self._dataset_repo.get_by_id(dataset_id)
        if dataset is None:
            raise EntityNotFoundError("Dataset", dataset_id)

        return DatasetDTO.from_domain(dataset)
