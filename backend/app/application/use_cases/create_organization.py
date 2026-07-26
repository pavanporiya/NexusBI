"""Create organization use case."""

from __future__ import annotations

import uuid

from app.application.dto.organization_dto import CreateOrganizationDTO, OrganizationDTO
from app.core.exceptions import DuplicateEntityError
from app.domain.entities.organization import Organization
from app.domain.repositories.organization_repository import IOrganizationRepository


class CreateOrganizationUseCase:
    """Orchestrates creation of a new enterprise organization."""

    def __init__(self, organization_repository: IOrganizationRepository) -> None:
        self._org_repo = organization_repository

    def execute(self, dto: CreateOrganizationDTO) -> OrganizationDTO:
        """Execute organization creation."""
        existing = self._org_repo.get_by_slug(dto.slug)
        if existing is not None:
            raise DuplicateEntityError("Organization", dto.slug)

        org_id = f"org-{uuid.uuid4()}"
        organization = Organization(
            id=org_id,
            name=dto.name,
            slug=dto.slug,
        )

        saved = self._org_repo.save(organization)
        return OrganizationDTO.from_domain(saved)
