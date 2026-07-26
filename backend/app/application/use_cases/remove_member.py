"""Remove member use case."""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.membership_repository import IMembershipRepository
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class RemoveMemberUseCase:
    """Orchestrates removing a user member from a workspace."""

    def __init__(
        self,
        membership_repository: IMembershipRepository,
        workspace_repository: IWorkspaceRepository,
    ) -> None:
        self._membership_repo = membership_repository
        self._workspace_repo = workspace_repository

    def execute(self, workspace_id: str, user_id: str) -> None:
        """Execute removing member from workspace."""
        ws = self._workspace_repo.get_by_id(workspace_id)
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)

        membership = self._membership_repo.get_by_workspace_and_user(
            workspace_id, user_id
        )
        if membership is None:
            raise EntityNotFoundError(
                "Membership", f"workspace:{workspace_id}, user:{user_id}"
            )

        self._membership_repo.delete(membership.id)
