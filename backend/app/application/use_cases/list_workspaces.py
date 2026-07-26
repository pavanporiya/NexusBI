"""List workspaces use case."""

from __future__ import annotations

import math

from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.workspace_dto import WorkspaceDTO
from app.domain.repositories.workspace_repository import IWorkspaceRepository


class ListWorkspacesUseCase:
    """Orchestrates paginated listing of workspaces."""

    def __init__(self, workspace_repository: IWorkspaceRepository) -> None:
        self._workspace_repo = workspace_repository

    def execute(
        self, organization_id: str | None = None, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[WorkspaceDTO]:
        """Execute paginated listing of workspaces."""
        if organization_id:
            items, total = self._workspace_repo.list_by_organization_id(
                organization_id, page=page, page_size=page_size
            )
        else:
            items, total = self._workspace_repo.list_all(page=page, page_size=page_size)

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        dtos = [WorkspaceDTO.from_domain(ws) for ws in items]
        return PaginatedResponse[WorkspaceDTO](
            items=dtos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
