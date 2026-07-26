"""Update member role use case."""

from __future__ import annotations

from app.application.dto.membership_dto import MembershipDTO, UpdateMemberRoleDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.membership_repository import IMembershipRepository
from app.domain.repositories.role_repository import IRoleRepository
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class UpdateMemberRoleUseCase:
    """Orchestrates updating a user member's assigned role in a workspace."""

    def __init__(
        self,
        membership_repository: IMembershipRepository,
        workspace_repository: IWorkspaceRepository,
        role_repository: IRoleRepository,
    ) -> None:
        self._membership_repo = membership_repository
        self._workspace_repo = workspace_repository
        self._role_repo = role_repository

    def execute(
        self, workspace_id: str, user_id: str, dto: UpdateMemberRoleDTO
    ) -> MembershipDTO:
        """Execute member role update in workspace."""
        ws = self._workspace_repo.get_by_id(workspace_id)
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)

        role = self._role_repo.get_by_id(dto.role_id)
        if role is None:
            raise EntityNotFoundError("Role", dto.role_id)

        membership = self._membership_repo.get_by_workspace_and_user(
            workspace_id, user_id
        )
        if membership is None:
            raise EntityNotFoundError(
                "Membership", f"workspace:{workspace_id}, user:{user_id}"
            )

        membership.update_role(dto.role_id)
        saved = self._membership_repo.save(membership)
        return MembershipDTO.from_domain(saved)
