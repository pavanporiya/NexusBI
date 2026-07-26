"""Report repository port interface.

Defines the contract for report persistence, query filtering, and retrieval.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.report import Report
from app.domain.value_objects.filter_params import FilterParams


@runtime_checkable
class IReportRepository(Protocol):
    """Port interface for persisting and fetching Report entities."""

    def get_by_id(self, report_id: str) -> Report | None:
        """Fetch a Report by its unique ID."""
        ...

    def save(self, report: Report) -> Report:
        """Persist a new Report or update an existing one."""
        ...

    def delete(self, report_id: str) -> bool:
        """Permanently remove a Report from persistence."""
        ...

    def list(self, params: FilterParams) -> tuple[list[Report], int]:
        """Fetch a paginated/filtered list of Reports with total count."""
        ...
