"""Dashboard repository port interface.

Defines the contract for dashboard persistence, query filtering, and retrieval.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.dashboard import Dashboard
from app.domain.value_objects.filter_params import FilterParams


@runtime_checkable
class IDashboardRepository(Protocol):
    """Port interface for persisting and fetching Dashboard entities."""

    def get_by_id(self, dashboard_id: str) -> Dashboard | None:
        """Fetch a Dashboard by its unique ID."""
        ...

    def save(self, dashboard: Dashboard) -> Dashboard:
        """Persist a new Dashboard or update an existing one."""
        ...

    def delete(self, dashboard_id: str) -> bool:
        """Permanently remove a Dashboard from persistence."""
        ...

    def list(self, params: FilterParams) -> tuple[list[Dashboard], int]:
        """Fetch a paginated/filtered list of Dashboards with total count."""
        ...
