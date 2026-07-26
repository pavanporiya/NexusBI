"""Dashboard Layout Value Objects.

Provides strongly typed domain representations for dashboard widget positions,
filters, widgets, and full layout configurations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class WidgetPosition:
    """Widget grid position and dimension value object.

    Attributes
    ----------
    x : int
        Grid column offset (x >= 0).
    y : int
        Grid row offset (y >= 0).
    w : int
        Grid width (w > 0).
    h : int
        Grid height (h > 0).
    """

    x: int
    y: int
    w: int
    h: int

    def __post_init__(self) -> None:
        """Enforce non-negative position offsets and positive dimensions."""
        if not isinstance(self.x, int) or self.x < 0:
            raise DomainValidationError(
                f"Widget position x must be a non-negative integer, got {self.x}"
            )
        if not isinstance(self.y, int) or self.y < 0:
            raise DomainValidationError(
                f"Widget position y must be a non-negative integer, got {self.y}"
            )
        if not isinstance(self.w, int) or self.w <= 0:
            raise DomainValidationError(
                f"Widget width w must be a positive integer (> 0), got {self.w}"
            )
        if not isinstance(self.h, int) or self.h <= 0:
            raise DomainValidationError(
                f"Widget height h must be a positive integer (> 0), got {self.h}"
            )

    def to_dict(self) -> dict[str, int]:
        """Serialize widget position to a dictionary."""
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WidgetPosition:
        """Construct WidgetPosition from a dictionary."""
        if not isinstance(data, dict):
            raise DomainValidationError(
                "WidgetPosition position data must be a dictionary"
            )
        try:
            x = int(data.get("x", 0))
            y = int(data.get("y", 0))
            w = int(data.get("w", 1))
            h = int(data.get("h", 1))
        except (ValueError, TypeError) as exc:
            raise DomainValidationError(
                f"Invalid integer position values: {exc}"
            ) from exc
        return cls(x=x, y=y, w=w, h=h)


@dataclass(frozen=True, slots=True)
class DashboardFilter:
    """Interactive filter control configuration value object."""

    id: str
    field: str
    operator: str
    value: Any = None

    def __post_init__(self) -> None:
        """Validate dashboard filter invariants."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Dashboard filter id must not be empty")
        if not self.field or not self.field.strip():
            raise DomainValidationError("Dashboard filter field must not be empty")
        if not self.operator or not self.operator.strip():
            raise DomainValidationError("Dashboard filter operator must not be empty")

        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "field", self.field.strip())
        object.__setattr__(self, "operator", self.operator.strip())

    def to_dict(self) -> dict[str, Any]:
        """Serialize filter to dictionary."""
        return {
            "id": self.id,
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashboardFilter:
        """Construct DashboardFilter from dictionary."""
        if not isinstance(data, dict):
            raise DomainValidationError("DashboardFilter data must be a dictionary")
        return cls(
            id=str(data.get("id", "")),
            field=str(data.get("field", "")),
            operator=str(data.get("operator", "")),
            value=data.get("value"),
        )


@dataclass(frozen=True, slots=True)
class DashboardWidget:
    """Dashboard widget item value object."""

    id: str
    type: str
    title: str
    position: WidgetPosition
    config: dict[str, Any] = field(default_factory=dict)
    query: str | None = None

    def __post_init__(self) -> None:
        """Validate dashboard widget invariants."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Widget id must not be empty")
        if not self.type or not self.type.strip():
            raise DomainValidationError("Widget type must not be empty")
        if not self.title or not self.title.strip():
            raise DomainValidationError("Widget title must not be empty")
        if not isinstance(self.position, WidgetPosition):
            raise DomainValidationError(
                "Widget position must be a WidgetPosition instance"
            )

        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "type", self.type.strip())
        object.__setattr__(self, "title", self.title.strip())

    def to_dict(self) -> dict[str, Any]:
        """Serialize widget to dictionary."""
        res: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "position": self.position.to_dict(),
            "config": dict(self.config or {}),
        }
        if self.query is not None:
            res["query"] = self.query
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashboardWidget:
        """Construct DashboardWidget from dictionary."""
        if not isinstance(data, dict):
            raise DomainValidationError("DashboardWidget data must be a dictionary")

        widget_id = str(data.get("id", ""))
        widget_type = str(data.get("type", "chart"))
        widget_title = str(data.get("title", f"Widget {widget_id}"))

        pos_data = data.get("position")
        if isinstance(pos_data, dict):
            pos = WidgetPosition.from_dict(pos_data)
        elif isinstance(pos_data, WidgetPosition):
            pos = pos_data
        else:
            pos = WidgetPosition(x=0, y=0, w=6, h=4)

        config = (
            dict(data.get("config", {})) if isinstance(data.get("config"), dict) else {}
        )
        query = data.get("query")

        return cls(
            id=widget_id,
            type=widget_type,
            title=widget_title,
            position=pos,
            config=config,
            query=str(query) if query is not None else None,
        )


@dataclass(frozen=True, slots=True)
class DashboardLayout:
    """Aggregate Dashboard layout value object.

    Contains widget definitions, grid columns, theme, and optional filters.
    """

    widgets: tuple[DashboardWidget, ...] = field(default_factory=tuple)
    filters: tuple[DashboardFilter, ...] = field(default_factory=tuple)
    columns: int = 12
    theme: str = "light"
    extra_config: dict[str, Any] = field(default_factory=dict)
    raw_dict: dict[str, Any] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Enforce layout invariants (column bounds, duplicate IDs)."""
        if not isinstance(self.columns, int) or self.columns <= 0:
            raise DomainValidationError(
                f"Layout columns must be a positive integer (> 0), got {self.columns}"
            )

        if isinstance(self.widgets, list):
            object.__setattr__(self, "widgets", tuple(self.widgets))
        if isinstance(self.filters, list):
            object.__setattr__(self, "filters", tuple(self.filters))

        seen_widget_ids: set[str] = set()
        for w in self.widgets:
            if w.id in seen_widget_ids:
                raise DomainValidationError(
                    f"Duplicate widget ID '{w.id}' in dashboard layout"
                )
            seen_widget_ids.add(w.id)

        seen_filter_ids: set[str] = set()
        for f in self.filters:
            if f.id in seen_filter_ids:
                raise DomainValidationError(
                    f"Duplicate filter ID '{f.id}' in dashboard layout"
                )
            seen_filter_ids.add(f.id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize complete layout to dictionary for JSON compatibility."""
        if self.raw_dict is not None:
            return dict(self.raw_dict)

        res: dict[str, Any] = dict(self.extra_config or {})
        if self.widgets:
            res["widgets"] = [w.to_dict() for w in self.widgets]
        if self.filters:
            res["filters"] = [f.to_dict() for f in self.filters]
        res["columns"] = self.columns
        res["theme"] = self.theme
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashboardLayout:
        """Construct DashboardLayout from dictionary."""
        if not isinstance(data, dict):
            raise DomainValidationError("DashboardLayout data must be a dictionary")

        raw_data = dict(data)
        widgets_data = raw_data.pop("widgets", [])
        filters_data = raw_data.pop("filters", [])
        columns = int(raw_data.pop("columns", 12))
        theme = str(raw_data.pop("theme", "light"))

        parsed_widgets: list[DashboardWidget] = []
        if isinstance(widgets_data, list):
            for item in widgets_data:
                if isinstance(item, DashboardWidget):
                    parsed_widgets.append(item)
                elif isinstance(item, str):
                    parsed_widgets.append(DashboardWidget.from_dict({"id": item}))
                elif isinstance(item, (int, float)):
                    parsed_widgets.append(DashboardWidget.from_dict({"id": str(item)}))
                elif isinstance(item, dict):
                    parsed_widgets.append(DashboardWidget.from_dict(item))

        parsed_filters: list[DashboardFilter] = []
        if isinstance(filters_data, list):
            for item in filters_data:
                if isinstance(item, DashboardFilter):
                    parsed_filters.append(item)
                elif isinstance(item, dict):
                    parsed_filters.append(DashboardFilter.from_dict(item))

        return cls(
            widgets=tuple(parsed_widgets),
            filters=tuple(parsed_filters),
            columns=columns,
            theme=theme,
            extra_config=raw_data,
            raw_dict=dict(data),
        )
