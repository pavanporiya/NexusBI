"""Update Dataset Use Case."""

from __future__ import annotations

from app.application.dto.dataset_dto import DatasetDTO, UpdateDatasetDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dataset_repository import IDatasetRepository


class UpdateDatasetUseCase:
    """Orchestrates updating an existing dataset."""

    def __init__(self, dataset_repository: IDatasetRepository) -> None:
        self._dataset_repo = dataset_repository

    def execute(self, dataset_id: str, dto: UpdateDatasetDTO) -> DatasetDTO:
        """Update dataset attributes.

        Raises
        ------
        EntityNotFoundError
            If dataset with dataset_id does not exist.
        """
        dataset = self._dataset_repo.get_by_id(dataset_id)
        if dataset is None:
            raise EntityNotFoundError("Dataset", dataset_id)

        dataset.update(
            name=dto.name,
            description=dto.description,
            source_type=dto.source_type,
            query_or_table=dto.query_or_table,
            object_type=dto.object_type,
            object_name=dto.object_name,
            sql_query=dto.sql_query,
            connection_id=dto.connection_id,
            schema_metadata=dto.schema_metadata,
            is_active=dto.is_active,
        )
        saved = self._dataset_repo.save(dataset)

        return DatasetDTO.from_domain(saved)
