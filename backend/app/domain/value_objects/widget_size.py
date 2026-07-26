"""WidgetSize domain value object.

Represents grid width and height dimensions for a widget.
Enforces positive dimension invariants (width > 0, height > 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class WidgetSize:
    """Widget grid dimension size value object.

    Attributes
    ----------
    width : int
        Grid width dimension (width > 0).
    height : int
        Grid height dimension (height > 0).
    """

    width: int
    height: int

    def __post_init__(self) -> None:
        """Enforce positive width and height dimension invariants."""
        if not isinstance(self.width, int) or self.width <= 0:
            raise DomainValidationError(
                f"Widget width must be a positive integer (> 0), got {self.width}"
            )
        if not isinstance(self.height, int) or self.height <= 0:
            raise DomainValidationError(
                f"Widget height must be a positive integer (> 0), got {self.height}"
            )

    def to_dict(self) -> dict[str, int]:
        """Serialize widget size to dictionary."""
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | WidgetSize) -> WidgetSize:
        """Construct WidgetSize from dictionary or instance."""
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise DomainValidationError("WidgetSize data must be a dictionary")
        try:
            width = int(data.get("width", 1))
            height = int(data.get("height", 1))
        except (ValueError, TypeError) as exc:
            raise DomainValidationError(f"Invalid integer size values: {exc}") from exc
        return cls(width=width, height=height)
