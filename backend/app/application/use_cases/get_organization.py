"""Get organization use case."""

from __future__ import annotations

from app.application.dto.organization_dto import OrganizationDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.organization_repository import IOrganizationRepository


class GetOrganizationUseCase:
    """Orchestrates retrieval of an enterprise organization by ID."""

    def __init__(self, organization_repository: IOrganizationRepository) -> None:
        self._org_repo = organization_repository

    def execute(self, org_id: str) -> OrganizationDTO:
        """Execute organization retrieval by ID."""
        org = self._org_repo.get_by_id(org_id)
        if org is None:
            raise EntityNotFoundError("Organization", org_id)

        return OrganizationDTO.from_domain(org)
