"""Add member use case."""

from __future__ import annotations

import uuid

from app.application.dto.membership_dto import AddMemberDTO, MembershipDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.membership import Membership
from app.domain.repositories.membership_repository import IMembershipRepository
from app.domain.repositories.role_repository import IRoleRepository
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class AddMemberUseCase:
    """Orchestrates adding a user member to a workspace."""

    def __init__(
        self,
        membership_repository: IMembershipRepository,
        workspace_repository: IWorkspaceRepository,
        user_repository: IUserRepository,
        role_repository: IRoleRepository,
    ) -> None:
        self._membership_repo = membership_repository
        self._workspace_repo = workspace_repository
        self._user_repo = user_repository
        self._role_repo = role_repository

    def execute(self, workspace_id: str, dto: AddMemberDTO) -> MembershipDTO:
        """Execute adding member to workspace."""
        ws = self._workspace_repo.get_by_id(workspace_id)
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)

        user = self._user_repo.get_by_id(dto.user_id)
        if user is None:
            raise EntityNotFoundError("User", dto.user_id)

        role = self._role_repo.get_by_id(dto.role_id)
        if role is None:
            raise EntityNotFoundError("Role", dto.role_id)

        existing = self._membership_repo.get_by_workspace_and_user(
            workspace_id, dto.user_id
        )
        if existing is not None:
            raise DuplicateEntityError(
                "Membership", f"workspace:{workspace_id}, user:{dto.user_id}"
            )

        mem_id = f"mem-{uuid.uuid4()}"
        membership = Membership(
            id=mem_id,
            workspace_id=workspace_id,
            user_id=dto.user_id,
            role_id=dto.role_id,
        )

        saved = self._membership_repo.save(membership)
        return MembershipDTO.from_domain(saved)
