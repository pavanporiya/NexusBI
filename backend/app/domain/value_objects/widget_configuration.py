"""WidgetConfiguration domain value object.

Provides a strongly-typed container for widget rendering options, metrics,
dimensions, color schemes, filters, and custom parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class WidgetConfiguration:
    """Strongly typed widget configuration value object.

    Attributes
    ----------
    metrics : tuple[str, ...]
        Metric field names or aggregated expressions.
    dimensions : tuple[str, ...]
        Dimension field names for grouping/segmentation.
    filters : dict[str, Any]
        Filter criteria applied to widget data query.
    sort_by : str | None
        Field name to sort widget data.
    sort_order : str
        Sorting direction ('asc' or 'desc').
    limit : int | None
        Maximum rows/data points to render.
    options : dict[str, Any]
        Display options (e.g., colors, legends, axis labels, text content).
    """

    metrics: tuple[str, ...] = field(default_factory=tuple)
    dimensions: tuple[str, ...] = field(default_factory=tuple)
    filters: dict[str, Any] = field(default_factory=dict)
    sort_by: str | None = None
    sort_order: str = "asc"
    limit: int | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if isinstance(self.metrics, list):
            object.__setattr__(self, "metrics", tuple(self.metrics))
        if isinstance(self.dimensions, list):
            object.__setattr__(self, "dimensions", tuple(self.dimensions))

        if self.limit is not None and (
            not isinstance(self.limit, int) or self.limit <= 0
        ):
            raise DomainValidationError(
                "Widget configuration limit must be a positive integer, "
                f"got {self.limit}"
            )

        if self.sort_order not in ("asc", "desc"):
            raise DomainValidationError(
                "Widget configuration sort_order must be 'asc' or 'desc', "
                f"got {self.sort_order}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to a dictionary."""
        res: dict[str, Any] = {
            "metrics": list(self.metrics),
            "dimensions": list(self.dimensions),
            "filters": dict(self.filters or {}),
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "options": dict(self.options or {}),
        }
        if self.limit is not None:
            res["limit"] = self.limit
        return res

    @classmethod
    def from_dict(
        cls, data: dict[str, Any] | WidgetConfiguration | None
    ) -> WidgetConfiguration:
        """Construct WidgetConfiguration from a dictionary or instance."""
        if data is None:
            return cls()
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise DomainValidationError("WidgetConfiguration data must be a dictionary")

        metrics = data.get("metrics", [])
        if isinstance(metrics, str):
            metrics = [metrics]
        elif not isinstance(metrics, (list, tuple)):
            metrics = []

        dimensions = data.get("dimensions", [])
        if isinstance(dimensions, str):
            dimensions = [dimensions]
        elif not isinstance(dimensions, (list, tuple)):
            dimensions = []

        filters = data.get("filters")
        if not isinstance(filters, dict):
            filters = {}

        options = data.get("options")
        if not isinstance(options, dict):
            options = {}

        # Preserve top-level keys not in explicitly named fields inside options
        known_keys = {
            "metrics",
            "dimensions",
            "filters",
            "sort_by",
            "sort_order",
            "limit",
            "options",
        }
        for k, v in data.items():
            if k not in known_keys and k not in options:
                options[k] = v

        sort_by = data.get("sort_by")
        sort_order = str(data.get("sort_order", "asc")).lower()
        limit = data.get("limit")

        return cls(
            metrics=tuple(str(m) for m in metrics),
            dimensions=tuple(str(d) for d in dimensions),
            filters=filters,
            sort_by=str(sort_by) if sort_by is not None else None,
            sort_order=sort_order,
            limit=int(limit) if limit is not None else None,
            options=options,
        )
