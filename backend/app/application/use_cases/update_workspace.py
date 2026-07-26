"""Update workspace use case."""

from __future__ import annotations

from app.application.dto.workspace_dto import UpdateWorkspaceDTO, WorkspaceDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class UpdateWorkspaceUseCase:
    """Orchestrates updating an existing workspace."""

    def __init__(self, workspace_repository: IWorkspaceRepository) -> None:
        self._workspace_repo = workspace_repository

    def execute(self, workspace_id: str, dto: UpdateWorkspaceDTO) -> WorkspaceDTO:
        """Execute workspace update."""
        ws = self._workspace_repo.get_by_id(workspace_id)
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)

        if dto.slug is not None and dto.slug.strip().lower() != ws.slug:
            existing = self._workspace_repo.get_by_slug(ws.organization_id, dto.slug)
            if existing is not None and existing.id != workspace_id:
                raise DuplicateEntityError("Workspace", dto.slug)

        ws.update(
            name=dto.name,
            slug=dto.slug,
            description=dto.description,
            is_default=dto.is_default,
            is_active=dto.is_active,
        )

        saved = self._workspace_repo.save(ws)
        return WorkspaceDTO.from_domain(saved)
