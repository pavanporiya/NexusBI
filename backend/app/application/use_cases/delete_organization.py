"""Delete organization use case."""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.organization_repository import IOrganizationRepository


class DeleteOrganizationUseCase:
    """Orchestrates deletion of an enterprise organization."""

    def __init__(self, organization_repository: IOrganizationRepository) -> None:
        self._org_repo = organization_repository

    def execute(self, org_id: str) -> None:
        """Execute organization deletion."""
        org = self._org_repo.get_by_id(org_id)
        if org is None:
            raise EntityNotFoundError("Organization", org_id)

        self._org_repo.delete(org_id)
