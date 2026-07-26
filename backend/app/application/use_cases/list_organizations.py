"""List organizations use case."""

from __future__ import annotations

import math

from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.organization_dto import OrganizationDTO
from app.domain.repositories.organization_repository import IOrganizationRepository


class ListOrganizationsUseCase:
    """Orchestrates paginated listing of enterprise organizations."""

    def __init__(self, organization_repository: IOrganizationRepository) -> None:
        self._org_repo = organization_repository

    def execute(
        self, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[OrganizationDTO]:
        """Execute paginated listing of organizations."""
        items, total = self._org_repo.list_all(page=page, page_size=page_size)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        dtos = [OrganizationDTO.from_domain(org) for org in items]
        return PaginatedResponse[OrganizationDTO](
            items=dtos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
