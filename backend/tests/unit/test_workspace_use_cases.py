"""Unit tests for Workspace use cases."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto.organization_dto import CreateOrganizationDTO
from app.application.dto.workspace_dto import CreateWorkspaceDTO, UpdateWorkspaceDTO
from app.application.use_cases.create_organization import CreateOrganizationUseCase
from app.application.use_cases.create_workspace import CreateWorkspaceUseCase
from app.application.use_cases.delete_workspace import DeleteWorkspaceUseCase
from app.application.use_cases.get_workspace import GetWorkspaceUseCase
from app.application.use_cases.list_workspaces import ListWorkspacesUseCase
from app.application.use_cases.update_workspace import UpdateWorkspaceUseCase
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.infrastructure.database.base import Base
from app.infrastructure.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
)
from app.infrastructure.repositories.workspace_repository import (
    SQLAlchemyWorkspaceRepository,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    """In-memory SQLite session fixture."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_workspace_use_cases(db_session: Session) -> None:
    org_repo = SQLAlchemyOrganizationRepository(db_session)
    ws_repo = SQLAlchemyWorkspaceRepository(db_session)

    org_uc = CreateOrganizationUseCase(org_repo)
    org = org_uc.execute(CreateOrganizationDTO(name="Org WS", slug="org-ws"))

    create_uc = CreateWorkspaceUseCase(ws_repo, org_repo)
    get_uc = GetWorkspaceUseCase(ws_repo)
    update_uc = UpdateWorkspaceUseCase(ws_repo)
    list_uc = ListWorkspacesUseCase(ws_repo)
    delete_uc = DeleteWorkspaceUseCase(ws_repo)

    # 1. Create Workspace
    dto = CreateWorkspaceDTO(
        organization_id=org.id,
        name="Workspace 1",
        slug="workspace-1",
        description="First workspace",
    )
    created = create_uc.execute(dto)
    assert created.name == "Workspace 1"
    assert created.organization_id == org.id

    # Duplicate slug error in same org
    with pytest.raises(DuplicateEntityError):
        create_uc.execute(dto)

    # Non-existent org error
    with pytest.raises(EntityNotFoundError):
        create_uc.execute(
            CreateWorkspaceDTO(organization_id="non-existent", name="WS", slug="ws")
        )

    # 2. Get Workspace
    fetched = get_uc.execute(created.id)
    assert fetched.id == created.id

    # 3. Update Workspace
    updated = update_uc.execute(
        created.id, UpdateWorkspaceDTO(name="Workspace 1 Updated")
    )
    assert updated.name == "Workspace 1 Updated"

    # 4. List Workspaces
    paginated = list_uc.execute(organization_id=org.id)
    assert paginated.total == 1
    assert paginated.items[0].id == created.id

    # 5. Delete Workspace
    delete_uc.execute(created.id)

    with pytest.raises(EntityNotFoundError):
        get_uc.execute(created.id)
