"""Organization Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.entities.organization import Organization


class OrganizationDTO(BaseModel):
    """Data transfer object representing an Organization domain entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(description="Unique Organization identifier")
    name: str = Field(description="Organization display name")
    slug: str = Field(description="URL-friendly unique slug identifier")
    is_active: bool = Field(default=True, description="Active status flag")
    created_at: datetime = Field(description="UTC timestamp of creation")
    updated_at: datetime = Field(description="UTC timestamp of last update")

    @classmethod
    def from_domain(cls, entity: Organization) -> OrganizationDTO:
        """Construct OrganizationDTO from Organization domain entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            slug=entity.slug,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class CreateOrganizationDTO(BaseModel):
    """Data transfer object for creating an Organization."""

    name: str = Field(
        min_length=1, max_length=256, description="Organization display name"
    )
    slug: str = Field(
        min_length=1, max_length=256, description="Unique URL-friendly slug"
    )


class UpdateOrganizationDTO(BaseModel):
    """Data transfer object for updating an Organization."""

    name: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated display name"
    )
    slug: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated slug"
    )
    is_active: bool | None = Field(
        default=None, description="Updated active status flag"
    )
