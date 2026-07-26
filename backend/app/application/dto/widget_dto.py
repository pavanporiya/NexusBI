"""Widget Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.entities.widget import Widget


class WidgetPositionDTO(BaseModel):
    """Data transfer object for widget grid position."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    row: int = Field(default=0, ge=0, description="Grid row offset (row >= 0)")
    column: int = Field(default=0, ge=0, description="Grid column offset (column >= 0)")


class WidgetSizeDTO(BaseModel):
    """Data transfer object for widget grid dimensions."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    width: int = Field(default=1, gt=0, description="Grid width dimension (width > 0)")
    height: int = Field(
        default=1, gt=0, description="Grid height dimension (height > 0)"
    )


class WidgetDTO(BaseModel):
    """Data transfer object representing a Widget entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(description="Unique Widget identifier")
    dashboard_id: str = Field(description="Parent dashboard identifier")
    dataset_id: str = Field(description="Referenced dataset identifier")
    title: str = Field(description="Widget display title")
    widget_type: str = Field(description="Widget visualization type string")
    position: WidgetPositionDTO = Field(description="Grid position (row, column)")
    size: WidgetSizeDTO = Field(description="Grid dimensions (width, height)")
    configuration: dict[str, Any] = Field(
        default_factory=dict, description="Strongly typed widget configuration"
    )
    refresh_interval: int = Field(default=0, description="Refresh interval in seconds")
    is_visible: bool = Field(default=True, description="Visibility status flag")
    created_at: datetime = Field(description="UTC creation timestamp")
    updated_at: datetime = Field(description="UTC last update timestamp")

    @classmethod
    def from_domain(cls, entity: Widget) -> WidgetDTO:
        """Construct WidgetDTO from a Widget domain entity."""
        return cls(
            id=entity.id,
            dashboard_id=entity.dashboard_id,
            dataset_id=entity.dataset_id,
            title=entity.title,
            widget_type=str(entity.widget_type),
            position=WidgetPositionDTO(
                row=entity.position.row, column=entity.position.column
            ),
            size=WidgetSizeDTO(width=entity.size.width, height=entity.size.height),
            configuration=entity.configuration.to_dict(),
            refresh_interval=entity.refresh_interval,
            is_visible=entity.is_visible,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class CreateWidgetDTO(BaseModel):
    """Data transfer object for creating a new Widget."""

    dashboard_id: str | None = Field(
        default=None,
        max_length=36,
        description="Parent dashboard ID (optional if provided in URL path)",
    )
    dataset_id: str = Field(
        min_length=1, max_length=36, description="Referenced dataset ID"
    )
    title: str = Field(min_length=1, max_length=256, description="Widget display title")
    widget_type: str = Field(
        min_length=1, max_length=64, description="Widget visualization type"
    )
    position: WidgetPositionDTO = Field(
        default_factory=WidgetPositionDTO, description="Grid row and column position"
    )
    size: WidgetSizeDTO = Field(
        default_factory=WidgetSizeDTO, description="Grid width and height dimensions"
    )
    configuration: dict[str, Any] = Field(
        default_factory=dict, description="Widget configuration parameters"
    )
    refresh_interval: int = Field(
        default=0, ge=0, description="Data refresh interval in seconds"
    )
    is_visible: bool = Field(default=True, description="Widget visibility flag")


class UpdateWidgetDTO(BaseModel):
    """Data transfer object for updating an existing Widget."""

    dataset_id: str | None = Field(
        default=None, min_length=1, max_length=36, description="Updated dataset ID"
    )
    title: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated display title"
    )
    widget_type: str | None = Field(
        default=None, min_length=1, max_length=64, description="Updated widget type"
    )
    position: WidgetPositionDTO | None = Field(
        default=None, description="Updated grid position"
    )
    size: WidgetSizeDTO | None = Field(default=None, description="Updated grid size")
    configuration: dict[str, Any] | None = Field(
        default=None, description="Updated configuration"
    )
    refresh_interval: int | None = Field(
        default=None, ge=0, description="Updated refresh interval"
    )
    is_visible: bool | None = Field(default=None, description="Updated visibility flag")


class MoveWidgetDTO(BaseModel):
    """Data transfer object for moving a Widget to a new position."""

    row: int = Field(ge=0, description="New grid row offset (>= 0)")
    column: int = Field(ge=0, description="New grid column offset (>= 0)")


class ResizeWidgetDTO(BaseModel):
    """Data transfer object for resizing a Widget."""

    width: int = Field(gt=0, description="New grid width dimension (> 0)")
    height: int = Field(gt=0, description="New grid height dimension (> 0)")


class ToggleVisibilityDTO(BaseModel):
    """Data transfer object for setting widget visibility."""

    is_visible: bool | None = Field(
        default=None, description="Explicit visibility status (or null to toggle)"
    )
