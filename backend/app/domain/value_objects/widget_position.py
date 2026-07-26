"""WidgetPosition domain value object.

Represents grid row and column offsets for a widget.
Enforces non-negative grid coordinate invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class WidgetPosition:
    """Widget grid position value object.

    Attributes
    ----------
    row : int
        Grid row offset (row >= 0).
    column : int
        Grid column offset (column >= 0).
    """

    row: int
    column: int

    def __post_init__(self) -> None:
        """Enforce non-negative row and column invariants."""
        if not isinstance(self.row, int) or self.row < 0:
            raise DomainValidationError(
                f"Widget position row must be a non-negative integer, got {self.row}"
            )
        if not isinstance(self.column, int) or self.column < 0:
            raise DomainValidationError(
                "Widget position column must be a non-negative integer, "
                f"got {self.column}"
            )

    def to_dict(self) -> dict[str, int]:
        """Serialize widget position to dictionary."""
        return {"row": self.row, "column": self.column}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | WidgetPosition) -> WidgetPosition:
        """Construct WidgetPosition from dictionary or instance."""
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise DomainValidationError("WidgetPosition data must be a dictionary")
        try:
            row = int(data.get("row", 0))
            column = int(data.get("column", 0))
        except (ValueError, TypeError) as exc:
            raise DomainValidationError(
                f"Invalid integer position values: {exc}"
            ) from exc
        return cls(row=row, column=column)
