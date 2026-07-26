"""Widget repository port interface.

Defines the contract for Widget persistence, retrieval, and dashboard queries.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.widget import Widget


@runtime_checkable
class IWidgetRepository(Protocol):
    """Port interface for persisting and fetching Widget entities."""

    def get_by_id(self, widget_id: str) -> Widget | None:
        """Fetch a Widget by its unique ID."""
        ...

    def list_by_dashboard_id(self, dashboard_id: str) -> list[Widget]:
        """Fetch all widgets contained inside a specific dashboard."""
        ...

    def get_by_dashboard_and_title(
        self, dashboard_id: str, title: str
    ) -> Widget | None:
        """Fetch a widget by dashboard ID and title (used for duplicate checks)."""
        ...

    def save(self, widget: Widget) -> Widget:
        """Persist a new Widget or update an existing one."""
        ...

    def delete(self, widget_id: str) -> bool:
        """Permanently remove a Widget from persistence."""
        ...
