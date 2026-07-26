"""Create Report Use Case."""

from __future__ import annotations

import uuid

from app.application.dto.report_dto import CreateReportDTO, ReportDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.report import Report
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.repositories.report_repository import IReportRepository


class CreateReportUseCase:
    """Orchestrates creating a new analytical report."""

    def __init__(
        self,
        report_repository: IReportRepository,
        dataset_repository: IDatasetRepository | None = None,
    ) -> None:
        self._report_repo = report_repository
        self._dataset_repo = dataset_repository

    def execute(self, dto: CreateReportDTO, owner_id: str) -> ReportDTO:
        """Create and persist a new Report entity.

        Parameters
        ----------
        dto : CreateReportDTO
            Request data payload.
        owner_id : str
            User ID of the creating user.

        Returns
        -------
        ReportDTO
            The created report DTO.

        Raises
        ------
        EntityNotFoundError
            If referenced dataset does not exist.
        """
        if self._dataset_repo is not None:
            dataset = self._dataset_repo.get_by_id(dto.dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dto.dataset_id)

        report_id = str(uuid.uuid4())
        report = Report(
            id=report_id,
            name=dto.name,
            dataset_id=dto.dataset_id,
            owner_id=owner_id,
            report_type=dto.report_type,
            output_format=dto.output_format,
            description=dto.description,
            schedule=dto.schedule,
            is_active=dto.is_active,
            query=dto.query or "",
            visualization_type=dto.visualization_type or "table",
            config=dto.config or {},
        )
        saved = self._report_repo.save(report)
        return ReportDTO.from_domain(saved)
