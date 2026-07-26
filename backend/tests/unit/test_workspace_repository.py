"""Unit tests for SQLAlchemyWorkspaceRepository."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.organization import Organization
from app.domain.entities.workspace import Workspace
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


def test_workspace_repository_crud(db_session: Session) -> None:
    org_repo = SQLAlchemyOrganizationRepository(db_session)
    ws_repo = SQLAlchemyWorkspaceRepository(db_session)

    # Setup parent org
    org = Organization(id="org-ws-test", name="Org WS Test", slug="org-ws-test")
    org_repo.save(org)

    # 1. Create & Save Workspace
    ws = Workspace(
        id="ws-test-1",
        organization_id="org-ws-test",
        name="Engineering Workspace",
        slug="engineering",
        description="Workspace for engineering",
    )
    saved = ws_repo.save(ws)
    assert saved.id == "ws-test-1"
    assert saved.organization_id == "org-ws-test"
    assert saved.slug == "engineering"

    # 2. Get by ID & Slug
    fetched_by_id = ws_repo.get_by_id("ws-test-1")
    assert fetched_by_id is not None
    assert fetched_by_id.name == "Engineering Workspace"

    fetched_by_slug = ws_repo.get_by_slug("org-ws-test", "engineering")
    assert fetched_by_slug is not None
    assert fetched_by_slug.id == "ws-test-1"

    # 3. List by Org
    items, total = ws_repo.list_by_organization_id("org-ws-test")
    assert total == 1
    assert items[0].id == "ws-test-1"

    # 4. Delete
    deleted = ws_repo.delete("ws-test-1")
    assert deleted is True
    assert ws_repo.get_by_id("ws-test-1") is None
