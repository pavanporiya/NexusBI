"""Unit tests for Membership use cases."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto.membership_dto import AddMemberDTO, UpdateMemberRoleDTO
from app.application.dto.organization_dto import CreateOrganizationDTO
from app.application.dto.workspace_dto import CreateWorkspaceDTO
from app.application.use_cases.add_member import AddMemberUseCase
from app.application.use_cases.create_organization import CreateOrganizationUseCase
from app.application.use_cases.create_workspace import CreateWorkspaceUseCase
from app.application.use_cases.list_members import ListMembersUseCase
from app.application.use_cases.remove_member import RemoveMemberUseCase
from app.application.use_cases.update_member_role import UpdateMemberRoleUseCase
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.role import Role
from app.domain.entities.user import User
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


def test_membership_use_cases(db_session: Session) -> None:
    org_repo = SQLAlchemyOrganizationRepository(db_session)
    ws_repo = SQLAlchemyWorkspaceRepository(db_session)
    mem_repo = SQLAlchemyMembershipRepository(db_session)
    user_repo = SQLAlchemyUserRepository(db_session)
    role_repo = SQLAlchemyRoleRepository(db_session)

    org_uc = CreateOrganizationUseCase(org_repo)
    ws_uc = CreateWorkspaceUseCase(ws_repo, org_repo)

    org = org_uc.execute(
        CreateOrganizationDTO(name="Org Mem UseCase", slug="org-mem-uc")
    )
    ws = ws_uc.execute(
        CreateWorkspaceDTO(
            organization_id=org.id, name="WS Mem UseCase", slug="ws-mem-uc"
        )
    )

    user = user_repo.save(
        User(id="usr-uc-1", email="ucuser@example.com", full_name="UC User")
    )
    role1 = role_repo.save(Role(id="role-uc-1", name="UC Role 1", description=""))
    role2 = role_repo.save(Role(id="role-uc-2", name="UC Role 2", description=""))

    add_uc = AddMemberUseCase(mem_repo, ws_repo, user_repo, role_repo)
    list_uc = ListMembersUseCase(mem_repo, ws_repo)
    update_role_uc = UpdateMemberRoleUseCase(mem_repo, ws_repo, role_repo)
    remove_uc = RemoveMemberUseCase(mem_repo, ws_repo)

    # 1. Add Member
    dto = AddMemberDTO(user_id=user.id, role_id=role1.id)
    added = add_uc.execute(ws.id, dto)
    assert added.workspace_id == ws.id
    assert added.user_id == user.id
    assert added.role_id == role1.id

    # Duplicate member error
    with pytest.raises(DuplicateEntityError):
        add_uc.execute(ws.id, dto)

    # Non-existent workspace/user/role errors
    with pytest.raises(EntityNotFoundError):
        add_uc.execute("non-existent", dto)
    with pytest.raises(EntityNotFoundError):
        add_uc.execute(ws.id, AddMemberDTO(user_id="non-existent", role_id=role1.id))
    with pytest.raises(EntityNotFoundError):
        add_uc.execute(ws.id, AddMemberDTO(user_id=user.id, role_id="non-existent"))

    # 2. List Members
    members = list_uc.execute(ws.id)
    assert members.total == 1
    assert members.items[0].user_id == user.id

    # 3. Update Member Role
    updated = update_role_uc.execute(
        ws.id, user.id, UpdateMemberRoleDTO(role_id=role2.id)
    )
    assert updated.role_id == role2.id

    # 4. Remove Member
    remove_uc.execute(ws.id, user.id)

    members_after = list_uc.execute(ws.id)
    assert members_after.total == 0
