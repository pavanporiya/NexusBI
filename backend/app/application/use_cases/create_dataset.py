"""Create Dataset Use Case."""

from __future__ import annotations

import uuid

from app.application.dto.dataset_dto import CreateDatasetDTO, DatasetDTO
from app.domain.entities.dataset import Dataset
from app.domain.repositories.dataset_repository import IDatasetRepository


class CreateDatasetUseCase:
    """Orchestrates creating a new dataset."""

    def __init__(self, dataset_repository: IDatasetRepository) -> None:
        self._dataset_repo = dataset_repository

    def execute(self, dto: CreateDatasetDTO, owner_id: str) -> DatasetDTO:
        """Create and persist a new Dataset entity."""
        dataset_id = str(uuid.uuid4())
        dataset = Dataset(
            id=dataset_id,
            name=dto.name,
            source_type=dto.source_type,
            query_or_table=dto.query_or_table,
            owner_id=owner_id,
            object_type=dto.object_type,
            object_name=dto.object_name,
            sql_query=dto.sql_query,
            connection_id=dto.connection_id,
            description=dto.description,
            schema_metadata=dto.schema_metadata,
            is_active=dto.is_active,
        )
        saved = self._dataset_repo.save(dataset)
        return DatasetDTO.from_domain(saved)
