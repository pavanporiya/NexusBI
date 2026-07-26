"""Widget entity ↔ ORM model mapper."""

from __future__ import annotations

from app.domain.entities.widget import Widget
from app.domain.enums import WidgetType
from app.domain.value_objects.widget_configuration import WidgetConfiguration
from app.domain.value_objects.widget_position import WidgetPosition
from app.domain.value_objects.widget_size import WidgetSize
from app.infrastructure.database.models import WidgetModel


class WidgetMapper:
    """Mapper between Widget entities and WidgetModel ORM objects."""

    @staticmethod
    def to_domain(model: WidgetModel) -> Widget:
        """Convert a WidgetModel ORM instance to a Widget domain entity."""
        return Widget(
            id=model.id,
            dashboard_id=model.dashboard_id,
            dataset_id=model.dataset_id,
            title=model.title,
            widget_type=WidgetType.from_str(model.widget_type),
            position=WidgetPosition(row=model.row, column=model.column),
            size=WidgetSize(width=model.width, height=model.height),
            configuration=WidgetConfiguration.from_dict(model.configuration or {}),
            refresh_interval=model.refresh_interval,
            is_visible=model.is_visible,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Widget) -> WidgetModel:
        """Convert a Widget domain entity to a new WidgetModel ORM instance."""
        return WidgetModel(
            id=entity.id,
            dashboard_id=entity.dashboard_id,
            dataset_id=entity.dataset_id,
            title=entity.title,
            widget_type=str(entity.widget_type),
            row=entity.position.row,
            column=entity.position.column,
            width=entity.size.width,
            height=entity.size.height,
            configuration=entity.configuration.to_dict(),
            refresh_interval=entity.refresh_interval,
            is_visible=entity.is_visible,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: WidgetModel, entity: Widget) -> None:
        """Update an existing WidgetModel from a Widget entity."""
        model.dataset_id = entity.dataset_id
        model.title = entity.title
        model.widget_type = str(entity.widget_type)
        model.row = entity.position.row
        model.column = entity.position.column
        model.width = entity.size.width
        model.height = entity.size.height
        model.configuration = entity.configuration.to_dict()
        model.refresh_interval = entity.refresh_interval
        model.is_visible = entity.is_visible
        model.updated_at = entity.updated_at
