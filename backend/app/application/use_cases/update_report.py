"""Update Report Use Case."""

from __future__ import annotations

from app.application.dto.report_dto import ReportDTO, UpdateReportDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.repositories.report_repository import IReportRepository


class UpdateReportUseCase:
    """Orchestrates updating an existing report."""

    def __init__(
        self,
        report_repository: IReportRepository,
        dataset_repository: IDatasetRepository | None = None,
    ) -> None:
        self._report_repo = report_repository
        self._dataset_repo = dataset_repository

    def execute(self, report_id: str, dto: UpdateReportDTO) -> ReportDTO:
        """Update report attributes.

        Raises
        ------
        EntityNotFoundError
            If report or dataset does not exist.
        """
        report = self._report_repo.get_by_id(report_id)
        if report is None:
            raise EntityNotFoundError("Report", report_id)

        if dto.dataset_id is not None and self._dataset_repo is not None:
            dataset = self._dataset_repo.get_by_id(dto.dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dto.dataset_id)

        report.update(
            name=dto.name,
            description=dto.description,
            dataset_id=dto.dataset_id,
            report_type=dto.report_type,
            output_format=dto.output_format,
            schedule=dto.schedule,
            is_active=dto.is_active,
            query=dto.query,
            visualization_type=dto.visualization_type,
            config=dto.config,
        )
        saved = self._report_repo.save(report)

        return ReportDTO.from_domain(saved)
