"""Dataset Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from app.domain.entities.dataset import Dataset


class DatasetDTO(BaseModel):
    """Data transfer object representing a Dataset entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(description="Unique Dataset identifier")
    name: str = Field(description="Dataset display name")
    source_type: str = Field(description="Source adapter type")
    object_type: str = Field(
        default="table",
        description="Dataset object type classification (table, view, query)",
    )
    object_name: str | None = Field(
        default=None, description="Physical table or view name"
    )
    sql_query: str | None = Field(default=None, description="Physical SQL query string")
    connection_id: str | None = Field(
        default=None, description="Optional connection reference ID"
    )
    query_or_table: str = Field(
        description="Backward compatibility field for SQL query or table name"
    )
    owner_id: str = Field(description="Owner user identifier")
    description: str | None = Field(default=None, description="Optional description")
    schema_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Schema metadata definitions JSON"
    )
    is_active: bool = Field(default=True, description="Active query flag")
    created_at: datetime = Field(description="UTC timestamp of creation")
    updated_at: datetime = Field(description="UTC timestamp of last update")

    @classmethod
    def from_domain(cls, entity: Dataset) -> DatasetDTO:
        """Construct DatasetDTO from a Dataset domain entity."""
        st_val = (
            entity.source_type.value
            if hasattr(entity.source_type, "value")
            else str(entity.source_type)
        )
        ot_val = (
            entity.object_type.value
            if hasattr(entity.object_type, "value")
            else str(entity.object_type)
        )
        return cls(
            id=entity.id,
            name=entity.name,
            source_type=st_val,
            object_type=ot_val,
            object_name=entity.object_name,
            sql_query=entity.sql_query,
            connection_id=entity.connection_id,
            query_or_table=entity.query_or_table,
            owner_id=entity.owner_id,
            description=entity.description,
            schema_metadata=entity.schema_metadata,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class CreateDatasetDTO(BaseModel):
    """Data transfer object for creating a new Dataset."""

    name: str = Field(min_length=1, max_length=256, description="Dataset display name")
    source_type: str = Field(
        min_length=1, max_length=64, description="Source adapter type"
    )
    object_type: str | None = Field(
        default=None, description="Dataset object classification (table, view, query)"
    )
    object_name: str | None = Field(
        default=None, description="Physical table or view name"
    )
    sql_query: str | None = Field(default=None, description="Physical SQL query string")
    connection_id: str | None = Field(
        default=None, description="Optional connection reference ID"
    )
    query_or_table: str | None = Field(
        default=None, description="Legacy SQL query or physical table name"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    schema_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Schema metadata definitions JSON"
    )
    is_active: bool = Field(default=True, description="Active status flag")

    @model_validator(mode="before")
    @classmethod
    def _validate_legacy_and_new_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            qt = data.get("query_or_table")
            obj_type = data.get("object_type")
            obj_name = data.get("object_name")
            sql = data.get("sql_query")

            if qt and not obj_type and not obj_name and not sql:
                stripped_qt = str(qt).strip()
                upper = stripped_qt.upper()
                if (
                    upper.startswith("SELECT")
                    or upper.startswith("WITH")
                    or " " in stripped_qt
                ):
                    data["object_type"] = "query"
                    data["sql_query"] = stripped_qt
                else:
                    data["object_type"] = "table"
                    data["object_name"] = stripped_qt
        return data


class UpdateDatasetDTO(BaseModel):
    """Data transfer object for updating an existing Dataset."""

    name: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated name"
    )
    source_type: str | None = Field(
        default=None, min_length=1, max_length=64, description="Updated source type"
    )
    object_type: str | None = Field(
        default=None, description="Updated object classification (table, view, query)"
    )
    object_name: str | None = Field(
        default=None, description="Updated physical table or view name"
    )
    sql_query: str | None = Field(
        default=None, description="Updated physical SQL query string"
    )
    connection_id: str | None = Field(
        default=None, description="Updated connection reference ID"
    )
    query_or_table: str | None = Field(
        default=None, min_length=1, description="Updated query or table name"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    schema_metadata: dict[str, Any] | None = Field(
        default=None, description="Updated schema metadata"
    )
    is_active: bool | None = Field(
        default=None, description="Updated active status flag"
    )
