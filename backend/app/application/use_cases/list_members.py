"""List members use case."""

from __future__ import annotations

import math

from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.membership_dto import MembershipDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.membership_repository import IMembershipRepository
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class ListMembersUseCase:
    """Orchestrates paginated listing of workspace members."""

    def __init__(
        self,
        membership_repository: IMembershipRepository,
        workspace_repository: IWorkspaceRepository,
    ) -> None:
        self._membership_repo = membership_repository
        self._workspace_repo = workspace_repository

    def execute(
        self, workspace_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[MembershipDTO]:
        """Execute paginated listing of workspace members."""
        ws = self._workspace_repo.get_by_id(workspace_id)
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)

        items, total = self._membership_repo.list_by_workspace_id(
            workspace_id, page=page, page_size=page_size
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        dtos = [MembershipDTO.from_domain(mem) for mem in items]
        return PaginatedResponse[MembershipDTO](
            items=dtos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
