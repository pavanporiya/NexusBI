"""Dashboard entity ↔ ORM model mapper."""

from __future__ import annotations

from app.domain.entities.dashboard import Dashboard
from app.domain.value_objects.dashboard_layout import DashboardLayout
from app.infrastructure.database.models import DashboardModel


class DashboardMapper:
    """Mapper between Dashboard entities and DashboardModel ORM objects."""

    @staticmethod
    def to_domain(model: DashboardModel) -> Dashboard:
        """Convert a DashboardModel ORM instance to a Dashboard domain entity."""
        raw_layout = dict(model.layout_json or {})
        return Dashboard(
            id=model.id,
            name=model.name,
            owner_id=model.owner_id,
            dataset_id=model.dataset_id,
            workspace_id=model.workspace_id or "",
            description=model.description,
            layout=DashboardLayout.from_dict(raw_layout),
            is_public=model.is_public,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Dashboard) -> DashboardModel:
        """Convert a Dashboard domain entity to a new DashboardModel ORM instance."""
        return DashboardModel(
            id=entity.id,
            name=entity.name,
            owner_id=entity.owner_id,
            dataset_id=entity.dataset_id,
            workspace_id=entity.workspace_id or None,
            description=entity.description,
            layout_json=entity.layout.to_dict(),
            is_public=entity.is_public,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: DashboardModel, entity: Dashboard) -> None:
        """Update an existing DashboardModel from a Dashboard entity."""
        model.name = entity.name
        model.dataset_id = entity.dataset_id
        model.workspace_id = entity.workspace_id or None
        model.description = entity.description
        model.layout_json = entity.layout.to_dict()
        model.is_public = entity.is_public
        model.is_active = entity.is_active
        model.updated_at = entity.updated_at
