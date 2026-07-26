"""Delete Dataset Use Case."""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dataset_repository import IDatasetRepository


class DeleteDatasetUseCase:
    """Orchestrates deleting a dataset."""

    def __init__(self, dataset_repository: IDatasetRepository) -> None:
        self._dataset_repo = dataset_repository

    def execute(self, dataset_id: str) -> None:
        """Delete a dataset by ID.

        Raises
        ------
        EntityNotFoundError
            If dataset with dataset_id does not exist.
        """
        deleted = self._dataset_repo.delete(dataset_id)
        if not deleted:
            raise EntityNotFoundError("Dataset", dataset_id)
