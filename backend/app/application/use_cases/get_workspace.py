"""Get workspace use case."""

from __future__ import annotations

from app.application.dto.workspace_dto import WorkspaceDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class GetWorkspaceUseCase:
    """Orchestrates retrieval of a workspace by ID."""

    def __init__(self, workspace_repository: IWorkspaceRepository) -> None:
        self._workspace_repo = workspace_repository

    def execute(self, workspace_id: str) -> WorkspaceDTO:
        """Execute workspace retrieval by ID."""
        ws = self._workspace_repo.get_by_id(workspace_id)
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)

        return WorkspaceDTO.from_domain(ws)
