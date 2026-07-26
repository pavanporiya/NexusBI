"""Dashboard Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from app.domain.entities.dashboard import Dashboard


class DashboardDTO(BaseModel):
    """Data transfer object representing a Dashboard entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(description="Unique Dashboard identifier")
    name: str = Field(description="Dashboard display title/name")
    owner_id: str = Field(description="Owner user identifier")
    dataset_id: str = Field(description="Referenced dataset identifier")
    description: str | None = Field(default=None, description="Optional description")
    layout_json: dict[str, Any] = Field(
        default_factory=dict, description="Widget layout JSON configuration"
    )
    is_public: bool = Field(default=False, description="Public visibility flag")
    is_active: bool = Field(default=True, description="Active status flag")
    created_at: datetime = Field(description="UTC timestamp of creation")
    updated_at: datetime = Field(description="UTC timestamp of last update")

    @property
    def layout_config(self) -> dict[str, Any]:
        """Backward compatibility property returning layout_json."""
        return self.layout_json

    @classmethod
    def from_domain(cls, entity: Dashboard) -> DashboardDTO:
        """Construct DashboardDTO from a Dashboard domain entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            owner_id=entity.owner_id,
            dataset_id=entity.dataset_id,
            description=entity.description,
            layout_json=entity.layout_json,
            is_public=entity.is_public,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class CreateDashboardDTO(BaseModel):
    """Data transfer object for creating a new Dashboard."""

    name: str = Field(
        min_length=1, max_length=256, description="Dashboard display name"
    )
    dataset_id: str = Field(
        min_length=1, max_length=36, description="Referenced dataset ID"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    layout_json: dict[str, Any] = Field(
        default_factory=dict, description="Widget layout JSON configuration"
    )
    is_public: bool = Field(default=False, description="Public visibility flag")
    is_active: bool = Field(default=True, description="Active status flag")

    @model_validator(mode="before")
    @classmethod
    def _handle_layout_config_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "layout_config" in data and "layout_json" not in data:
                data["layout_json"] = data["layout_config"]
        return data


class UpdateDashboardDTO(BaseModel):
    """Data transfer object for updating an existing Dashboard."""

    name: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated name"
    )
    dataset_id: str | None = Field(
        default=None, min_length=1, max_length=36, description="Updated dataset ID"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    layout_json: dict[str, Any] | None = Field(
        default=None, description="Updated layout configuration JSON"
    )
    is_public: bool | None = Field(
        default=None, description="Optional public visibility flag"
    )
    is_active: bool | None = Field(
        default=None, description="Optional active status flag"
    )

    @model_validator(mode="before")
    @classmethod
    def _handle_layout_config_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "layout_config" in data and "layout_json" not in data:
                data["layout_json"] = data["layout_config"]
        return data
