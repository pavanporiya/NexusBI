"""Workspace Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.entities.workspace import Workspace


class WorkspaceDTO(BaseModel):
    """Data transfer object representing a Workspace domain entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(description="Unique Workspace identifier")
    organization_id: str = Field(description="Parent Organization identifier")
    name: str = Field(description="Workspace display name")
    slug: str = Field(description="URL-friendly unique slug identifier")
    description: str | None = Field(default=None, description="Optional description")
    is_default: bool = Field(
        default=False, description="Organization default workspace flag"
    )
    is_active: bool = Field(default=True, description="Active status flag")
    created_at: datetime = Field(description="UTC timestamp of creation")
    updated_at: datetime = Field(description="UTC timestamp of last update")

    @classmethod
    def from_domain(cls, entity: Workspace) -> WorkspaceDTO:
        """Construct WorkspaceDTO from Workspace domain entity."""
        return cls(
            id=entity.id,
            organization_id=entity.organization_id,
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
            is_default=entity.is_default,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class CreateWorkspaceDTO(BaseModel):
    """Data transfer object for creating a Workspace."""

    organization_id: str = Field(
        min_length=1, max_length=64, description="Parent Organization ID"
    )
    name: str = Field(
        min_length=1, max_length=256, description="Workspace display name"
    )
    slug: str = Field(
        min_length=1, max_length=256, description="Unique URL-friendly slug"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    is_default: bool = Field(
        default=False, description="Set as organization default workspace"
    )


class UpdateWorkspaceDTO(BaseModel):
    """Data transfer object for updating a Workspace."""

    name: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated display name"
    )
    slug: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated slug"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    is_default: bool | None = Field(
        default=None, description="Updated default workspace flag"
    )
    is_active: bool | None = Field(
        default=None, description="Updated active status flag"
    )
