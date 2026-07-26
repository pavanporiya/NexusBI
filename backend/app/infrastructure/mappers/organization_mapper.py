"""Organization entity ↔ ORM model mapper."""

from __future__ import annotations

from app.domain.entities.organization import Organization
from app.infrastructure.database.models import OrganizationModel


class OrganizationMapper:
    """Mapper between Organization entities and OrganizationModel ORM objects."""

    @staticmethod
    def to_domain(model: OrganizationModel) -> Organization:
        """Convert OrganizationModel ORM instance to Organization entity."""
        return Organization(
            id=model.id,
            name=model.name,
            slug=model.slug,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Organization) -> OrganizationModel:
        """Convert Organization domain entity to new OrganizationModel instance."""
        return OrganizationModel(
            id=entity.id,
            name=entity.name,
            slug=entity.slug,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: OrganizationModel, entity: Organization) -> None:
        """Update an existing OrganizationModel from an Organization entity."""
        model.name = entity.name
        model.slug = entity.slug
        model.is_active = entity.is_active
        model.updated_at = entity.updated_at
