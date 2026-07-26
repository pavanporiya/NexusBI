"""Update organization use case."""

from __future__ import annotations

from app.application.dto.organization_dto import OrganizationDTO, UpdateOrganizationDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.repositories.organization_repository import IOrganizationRepository


class UpdateOrganizationUseCase:
    """Orchestrates updating an existing enterprise organization."""

    def __init__(self, organization_repository: IOrganizationRepository) -> None:
        self._org_repo = organization_repository

    def execute(self, org_id: str, dto: UpdateOrganizationDTO) -> OrganizationDTO:
        """Execute organization update."""
        org = self._org_repo.get_by_id(org_id)
        if org is None:
            raise EntityNotFoundError("Organization", org_id)

        if dto.slug is not None and dto.slug.strip().lower() != org.slug:
            existing = self._org_repo.get_by_slug(dto.slug)
            if existing is not None and existing.id != org_id:
                raise DuplicateEntityError("Organization", dto.slug)

        org.update(
            name=dto.name,
            slug=dto.slug,
            is_active=dto.is_active,
        )

        saved = self._org_repo.save(org)
        return OrganizationDTO.from_domain(saved)
