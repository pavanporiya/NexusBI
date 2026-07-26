"""SQLAlchemy implementation of the Workspace repository.

Fulfills the IWorkspaceRepository Protocol contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.workspace import Workspace
from app.infrastructure.database.models import WorkspaceModel
from app.infrastructure.mappers.workspace_mapper import WorkspaceMapper


class SQLAlchemyWorkspaceRepository:
    """Concrete IWorkspaceRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, workspace_id: str) -> Workspace | None:
        """Fetch a Workspace by its unique ID."""
        stmt = select(WorkspaceModel).where(WorkspaceModel.id == workspace_id)
        model = self._session.execute(stmt).scalars().first()
        return WorkspaceMapper.to_domain(model) if model else None

    def get_by_slug(self, organization_id: str, slug: str) -> Workspace | None:
        """Fetch a Workspace by organization ID and slug."""
        stmt = select(WorkspaceModel).where(
            WorkspaceModel.organization_id == organization_id,
            WorkspaceModel.slug == slug.strip().lower(),
        )
        model = self._session.execute(stmt).scalars().first()
        return WorkspaceMapper.to_domain(model) if model else None

    def save(self, workspace: Workspace) -> Workspace:
        """Persist a new Workspace or update an existing one."""
        existing = self._session.get(WorkspaceModel, workspace.id)
        if existing:
            WorkspaceMapper.update_model(existing, workspace)
            model = existing
        else:
            model = WorkspaceMapper.to_model(workspace)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return WorkspaceMapper.to_domain(model)

    def delete(self, workspace_id: str) -> bool:
        """Permanently remove a Workspace by ID."""
        model = self._session.get(WorkspaceModel, workspace_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list_by_organization_id(
        self, organization_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Workspace], int]:
        """Fetch a paginated list of Workspaces for an Organization with total count."""
        stmt = select(WorkspaceModel).where(
            WorkspaceModel.organization_id == organization_id
        )
        count_stmt = select(func.count()).where(
            WorkspaceModel.organization_id == organization_id
        )
        total = self._session.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(WorkspaceModel.created_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        models = self._session.execute(stmt).scalars().all()
        return [WorkspaceMapper.to_domain(m) for m in models], total

    def list_all(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Workspace], int]:
        """Fetch a paginated list of all Workspaces with total count."""
        stmt = select(WorkspaceModel)
        count_stmt = select(func.count()).select_from(WorkspaceModel)
        total = self._session.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(WorkspaceModel.created_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        models = self._session.execute(stmt).scalars().all()
        return [WorkspaceMapper.to_domain(m) for m in models], total
