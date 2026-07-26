"""Create workspace use case."""

from __future__ import annotations

import uuid

from app.application.dto.workspace_dto import CreateWorkspaceDTO, WorkspaceDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.workspace import Workspace
from app.domain.repositories.organization_repository import IOrganizationRepository
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class CreateWorkspaceUseCase:
    """Orchestrates creation of a new multi-tenant workspace within an organization."""

    def __init__(
        self,
        workspace_repository: IWorkspaceRepository,
        organization_repository: IOrganizationRepository,
    ) -> None:
        self._workspace_repo = workspace_repository
        self._org_repo = organization_repository

    def execute(self, dto: CreateWorkspaceDTO) -> WorkspaceDTO:
        """Execute workspace creation."""
        org = self._org_repo.get_by_id(dto.organization_id)
        if org is None:
            raise EntityNotFoundError("Organization", dto.organization_id)

        existing = self._workspace_repo.get_by_slug(dto.organization_id, dto.slug)
        if existing is not None:
            raise DuplicateEntityError("Workspace", dto.slug)

        ws_id = f"ws-{uuid.uuid4()}"
        workspace = Workspace(
            id=ws_id,
            organization_id=dto.organization_id,
            name=dto.name,
            slug=dto.slug,
            description=dto.description,
            is_default=dto.is_default,
        )

        saved = self._workspace_repo.save(workspace)
        return WorkspaceDTO.from_domain(saved)
