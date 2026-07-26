"""Unit tests for SQLAlchemyMembershipRepository."""

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.membership import Membership
from app.domain.entities.organization import Organization
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.entities.workspace import Workspace
from app.infrastructure.database.base import Base
from app.infrastructure.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)
from app.infrastructure.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
)
from app.infrastructure.repositories.role_repository import SQLAlchemyRoleRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
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


def test_membership_repository_crud(db_session: Session) -> None:
    org_repo = SQLAlchemyOrganizationRepository(db_session)
    ws_repo = SQLAlchemyWorkspaceRepository(db_session)
    user_repo = SQLAlchemyUserRepository(db_session)
    role_repo = SQLAlchemyRoleRepository(db_session)
    mem_repo = SQLAlchemyMembershipRepository(db_session)

    # Setup parent org, workspace, user, role
    org_repo.save(
        Organization(id="org-mem-test", name="Org Mem Test", slug="org-mem-test")
    )
    ws_repo.save(
        Workspace(
            id="ws-mem-test",
            organization_id="org-mem-test",
            name="WS Mem Test",
            slug="ws-mem-test",
        )
    )
    user_repo.save(
        User(
            id="user-mem-test",
            email="memuser@example.com",
            full_name="Mem User",
        )
    )
    role_repo.save(
        Role(
            id="role-mem-test",
            name="Mem Role",
            description="Role for membership test",
        )
    )

    # 1. Create & Save Membership
    mem = Membership(
        id="mem-test-1",
        workspace_id="ws-mem-test",
        user_id="user-mem-test",
        role_id="role-mem-test",
        joined_at=datetime.now(UTC),
    )
    saved = mem_repo.save(mem)
    assert saved.id == "mem-test-1"

    # 2. Get by ID & workspace/user
    fetched_by_id = mem_repo.get_by_id("mem-test-1")
    assert fetched_by_id is not None

    fetched = mem_repo.get_by_workspace_and_user("ws-mem-test", "user-mem-test")
    assert fetched is not None
    assert fetched.id == "mem-test-1"

    # 3. List
    items, total = mem_repo.list_by_workspace_id("ws-mem-test")
    assert total == 1
    assert items[0].id == "mem-test-1"

    # 4. Delete
    deleted = mem_repo.delete("mem-test-1")
    assert deleted is True
    assert mem_repo.get_by_id("mem-test-1") is None
