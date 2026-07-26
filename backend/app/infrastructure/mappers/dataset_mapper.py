"""Dataset entity ↔ ORM model mapper."""

from __future__ import annotations

from app.domain.entities.dataset import Dataset
from app.infrastructure.database.models import DatasetModel


class DatasetMapper:
    """Stateless mapper between Dataset domain entities and DatasetModel ORM objects."""

    @staticmethod
    def to_domain(model: DatasetModel) -> Dataset:
        """Convert a DatasetModel ORM instance to a Dataset domain entity."""
        return Dataset(
            id=model.id,
            name=model.name,
            source_type=model.source_type,
            workspace_id=model.workspace_id or "",
            query_or_table=model.query_or_table,
            owner_id=model.owner_id,
            object_type=model.object_type,
            object_name=model.object_name,
            sql_query=model.sql_query,
            connection_id=model.connection_id,
            description=model.description,
            schema_metadata=dict(model.schema_metadata or {}),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Dataset) -> DatasetModel:
        """Convert a Dataset domain entity to a new DatasetModel ORM instance."""
        source_type_val = (
            entity.source_type.value
            if hasattr(entity.source_type, "value")
            else str(entity.source_type)
        )
        object_type_val = (
            entity.object_type.value
            if hasattr(entity.object_type, "value")
            else str(entity.object_type)
        )
        return DatasetModel(
            id=entity.id,
            name=entity.name,
            source_type=source_type_val,
            workspace_id=entity.workspace_id or None,
            query_or_table=entity.query_or_table,
            object_type=object_type_val,
            object_name=entity.object_name,
            sql_query=entity.sql_query,
            connection_id=entity.connection_id,
            owner_id=entity.owner_id,
            description=entity.description,
            schema_metadata=dict(entity.schema_metadata or {}),
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: DatasetModel, entity: Dataset) -> None:
        """Update an existing DatasetModel ORM instance from a Dataset domain entity."""
        model.name = entity.name
        model.source_type = (
            entity.source_type.value
            if hasattr(entity.source_type, "value")
            else str(entity.source_type)
        )
        model.workspace_id = entity.workspace_id or None
        model.query_or_table = entity.query_or_table
        model.object_type = (
            entity.object_type.value
            if hasattr(entity.object_type, "value")
            else str(entity.object_type)
        )
        model.object_name = entity.object_name
        model.sql_query = entity.sql_query
        model.connection_id = entity.connection_id
        model.description = entity.description
        model.schema_metadata = dict(entity.schema_metadata or {})
        model.is_active = entity.is_active
        model.updated_at = entity.updated_at
