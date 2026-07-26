"""Delete Report Use Case."""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.report_repository import IReportRepository


class DeleteReportUseCase:
    """Orchestrates deleting a report."""

    def __init__(self, report_repository: IReportRepository) -> None:
        self._report_repo = report_repository

    def execute(self, report_id: str) -> None:
        """Delete a report by ID.

        Raises
        ------
        EntityNotFoundError
            If report with report_id does not exist.
        """
        deleted = self._report_repo.delete(report_id)
        if not deleted:
            raise EntityNotFoundError("Report", report_id)
