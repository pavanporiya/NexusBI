"""Workspace entity ↔ ORM model mapper."""

from __future__ import annotations

from app.domain.entities.workspace import Workspace
from app.infrastructure.database.models import WorkspaceModel


class WorkspaceMapper:
    """Mapper between Workspace entities and WorkspaceModel ORM objects."""

    @staticmethod
    def to_domain(model: WorkspaceModel) -> Workspace:
        """Convert a WorkspaceModel ORM instance to a Workspace domain entity."""
        return Workspace(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            is_default=model.is_default,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Workspace) -> WorkspaceModel:
        """Convert a Workspace domain entity to a new WorkspaceModel ORM instance."""
        return WorkspaceModel(
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

    @staticmethod
    def update_model(model: WorkspaceModel, entity: Workspace) -> None:
        """Update an existing WorkspaceModel from a Workspace entity."""
        model.name = entity.name
        model.slug = entity.slug
        model.description = entity.description
        model.is_default = entity.is_default
        model.is_active = entity.is_active
        model.updated_at = entity.updated_at
