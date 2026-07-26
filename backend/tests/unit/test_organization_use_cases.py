"""Unit tests for Organization use cases."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto.organization_dto import (
    CreateOrganizationDTO,
    UpdateOrganizationDTO,
)
from app.application.use_cases.create_organization import CreateOrganizationUseCase
from app.application.use_cases.delete_organization import DeleteOrganizationUseCase
from app.application.use_cases.get_organization import GetOrganizationUseCase
from app.application.use_cases.list_organizations import ListOrganizationsUseCase
from app.application.use_cases.update_organization import UpdateOrganizationUseCase
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.infrastructure.database.base import Base
from app.infrastructure.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
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


def test_organization_use_cases(db_session: Session) -> None:
    repo = SQLAlchemyOrganizationRepository(db_session)

    create_uc = CreateOrganizationUseCase(repo)
    get_uc = GetOrganizationUseCase(repo)
    update_uc = UpdateOrganizationUseCase(repo)
    list_uc = ListOrganizationsUseCase(repo)
    delete_uc = DeleteOrganizationUseCase(repo)

    # 1. Create Organization
    dto = CreateOrganizationDTO(name="Org One", slug="org-one")
    created = create_uc.execute(dto)
    assert created.name == "Org One"
    assert created.slug == "org-one"

    # Duplicate creation error
    with pytest.raises(DuplicateEntityError):
        create_uc.execute(dto)

    # 2. Get Organization
    fetched = get_uc.execute(created.id)
    assert fetched.id == created.id
    assert fetched.name == "Org One"

    # Get non-existent
    with pytest.raises(EntityNotFoundError):
        get_uc.execute("non-existent")

    # 3. Update Organization
    updated = update_uc.execute(
        created.id, UpdateOrganizationDTO(name="Org One Updated")
    )
    assert updated.name == "Org One Updated"

    # 4. List Organizations
    paginated = list_uc.execute(page=1, page_size=10)
    assert paginated.total >= 1
    assert any(o.id == created.id for o in paginated.items)

    # 5. Delete Organization
    delete_uc.execute(created.id)

    with pytest.raises(EntityNotFoundError):
        get_uc.execute(created.id)
