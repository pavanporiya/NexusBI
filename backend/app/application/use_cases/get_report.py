"""Get Report Use Case."""

from __future__ import annotations

from app.application.dto.report_dto import ReportDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.report_repository import IReportRepository


class GetReportUseCase:
    """Orchestrates loading a report by ID."""

    def __init__(self, report_repository: IReportRepository) -> None:
        self._report_repo = report_repository

    def execute(self, report_id: str) -> ReportDTO:
        """Retrieve a specific report by ID.

        Raises
        ------
        EntityNotFoundError
            If report with report_id does not exist.
        """
        report = self._report_repo.get_by_id(report_id)
        if report is None:
            raise EntityNotFoundError("Report", report_id)

        return ReportDTO.from_domain(report)
