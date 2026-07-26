"""Widget domain aggregate entity.

Represents a dashboard widget visualization bound to a dataset.
Enforces domain invariants and business rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.enums import WidgetType
from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.widget_configuration import WidgetConfiguration
from app.domain.value_objects.widget_position import WidgetPosition
from app.domain.value_objects.widget_size import WidgetSize


@dataclass(slots=True)
class Widget:
    """Represents a BI dashboard widget aggregate entity.

    Attributes
    ----------
    id : str
        UUID primary key.
    dashboard_id : str
        ID of parent dashboard.
    dataset_id : str
        ID of referenced dataset.
    title : str
        Display title of widget.
    widget_type : WidgetType
        Visualization classification enum.
    position : WidgetPosition
        Grid row and column position value object.
    size : WidgetSize
        Grid width and height dimension value object.
    configuration : WidgetConfiguration
        Strongly typed configuration value object.
    refresh_interval : int
        Automatic data refresh interval in seconds (>= 0).
    is_visible : bool
        Whether widget is visible on dashboard layout.
    created_at : datetime
        UTC creation timestamp.
    updated_at : datetime
        UTC last modification timestamp.
    """

    id: str
    dashboard_id: str
    dataset_id: str
    title: str
    widget_type: WidgetType
    position: WidgetPosition = field(
        default_factory=lambda: WidgetPosition(row=0, column=0)
    )
    size: WidgetSize = field(default_factory=lambda: WidgetSize(width=1, height=1))
    configuration: WidgetConfiguration = field(default_factory=WidgetConfiguration)
    refresh_interval: int = 0
    is_visible: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __init__(
        self,
        id: str,
        dashboard_id: str,
        dataset_id: str,
        title: str,
        widget_type: WidgetType | str,
        position: WidgetPosition | dict[str, Any] | None = None,
        size: WidgetSize | dict[str, Any] | None = None,
        configuration: WidgetConfiguration | dict[str, Any] | None = None,
        refresh_interval: int = 0,
        is_visible: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id.strip() if isinstance(id, str) else ""
        self.dashboard_id = (
            dashboard_id.strip() if isinstance(dashboard_id, str) else ""
        )
        self.dataset_id = dataset_id.strip() if isinstance(dataset_id, str) else ""
        self.title = title.strip() if isinstance(title, str) else ""
        self.refresh_interval = refresh_interval
        self.is_visible = is_visible
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

        # Parse WidgetType
        try:
            self.widget_type = WidgetType.from_str(widget_type)
        except (ValueError, TypeError) as exc:
            raise DomainValidationError(f"Invalid widget_type: {widget_type}") from exc

        # Parse position
        if isinstance(position, WidgetPosition):
            self.position = position
        elif isinstance(position, dict):
            self.position = WidgetPosition.from_dict(position)
        else:
            self.position = WidgetPosition(row=0, column=0)

        # Parse size
        if isinstance(size, WidgetSize):
            self.size = size
        elif isinstance(size, dict):
            self.size = WidgetSize.from_dict(size)
        else:
            self.size = WidgetSize(width=1, height=1)

        # Parse configuration
        if isinstance(configuration, WidgetConfiguration):
            self.configuration = configuration
        elif isinstance(configuration, dict):
            self.configuration = WidgetConfiguration.from_dict(configuration)
        else:
            self.configuration = WidgetConfiguration()

        self.__post_init__()

    def __post_init__(self) -> None:
        """Validate widget domain invariants."""
        if not self.id:
            raise DomainValidationError("Widget id must not be empty")
        if not self.dashboard_id:
            raise DomainValidationError("Widget dashboard_id must not be empty")
        if not self.dataset_id:
            raise DomainValidationError("Widget dataset_id must not be empty")
        if not self.title:
            raise DomainValidationError("Widget title must not be empty")

        if not isinstance(self.widget_type, WidgetType):
            try:
                self.widget_type = WidgetType.from_str(self.widget_type)
            except Exception as exc:
                raise DomainValidationError(
                    f"Invalid widget_type: {self.widget_type}"
                ) from exc

        if not isinstance(self.position, WidgetPosition):
            raise DomainValidationError(
                "Widget position must be a WidgetPosition instance"
            )

        if not isinstance(self.size, WidgetSize):
            raise DomainValidationError("Widget size must be a WidgetSize instance")

        if not isinstance(self.configuration, WidgetConfiguration):
            raise DomainValidationError(
                "Widget configuration must be a WidgetConfiguration instance"
            )

        if not isinstance(self.refresh_interval, int) or self.refresh_interval < 0:
            raise DomainValidationError(
                "Widget refresh_interval must be a non-negative integer"
            )

    def move(self, row: int, column: int) -> None:
        """Move widget to a new grid position (row, column)."""
        self.position = WidgetPosition(row=row, column=column)
        self.updated_at = datetime.now(UTC)

    def resize(self, width: int, height: int) -> None:
        """Resize widget to new grid dimensions (width, height)."""
        self.size = WidgetSize(width=width, height=height)
        self.updated_at = datetime.now(UTC)

    def toggle_visibility(self, visible: bool | None = None) -> None:
        """Toggle or explicitly set widget visibility."""
        if visible is None:
            self.is_visible = not self.is_visible
        else:
            self.is_visible = visible
        self.updated_at = datetime.now(UTC)

    def update(
        self,
        title: str | None = None,
        dataset_id: str | None = None,
        widget_type: WidgetType | str | None = None,
        position: WidgetPosition | dict[str, Any] | None = None,
        size: WidgetSize | dict[str, Any] | None = None,
        configuration: WidgetConfiguration | dict[str, Any] | None = None,
        refresh_interval: int | None = None,
        is_visible: bool | None = None,
    ) -> None:
        """Update widget attributes and refresh updated_at timestamp."""
        if title is not None:
            stripped = title.strip()
            if not stripped:
                raise DomainValidationError("Widget title must not be empty")
            self.title = stripped

        if dataset_id is not None:
            stripped_ds = dataset_id.strip()
            if not stripped_ds:
                raise DomainValidationError("Widget dataset_id must not be empty")
            self.dataset_id = stripped_ds

        if widget_type is not None:
            try:
                self.widget_type = WidgetType.from_str(widget_type)
            except Exception as exc:
                raise DomainValidationError(
                    f"Invalid widget_type: {widget_type}"
                ) from exc

        if position is not None:
            if isinstance(position, WidgetPosition):
                self.position = position
            elif isinstance(position, dict):
                self.position = WidgetPosition.from_dict(position)

        if size is not None:
            if isinstance(size, WidgetSize):
                self.size = size
            elif isinstance(size, dict):
                self.size = WidgetSize.from_dict(size)

        if configuration is not None:
            if isinstance(configuration, WidgetConfiguration):
                self.configuration = configuration
            elif isinstance(configuration, dict):
                self.configuration = WidgetConfiguration.from_dict(configuration)

        if refresh_interval is not None:
            if not isinstance(refresh_interval, int) or refresh_interval < 0:
                raise DomainValidationError(
                    "Widget refresh_interval must be a non-negative integer"
                )
            self.refresh_interval = refresh_interval

        if is_visible is not None:
            self.is_visible = is_visible

        self.__post_init__()
        self.updated_at = datetime.now(UTC)
