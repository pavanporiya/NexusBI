"""Delete workspace use case."""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class DeleteWorkspaceUseCase:
    """Orchestrates deletion of a workspace."""

    def __init__(self, workspace_repository: IWorkspaceRepository) -> None:
        self._workspace_repo = workspace_repository

    def execute(self, workspace_id: str) -> None:
        """Execute workspace deletion."""
        ws = self._workspace_repo.get_by_id(workspace_id)
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)

        self._workspace_repo.delete(workspace_id)
