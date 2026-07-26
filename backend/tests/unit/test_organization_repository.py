"""Unit tests for SQLAlchemyOrganizationRepository."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.organization import Organization
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


def test_organization_repository_crud(db_session: Session) -> None:
    repo = SQLAlchemyOrganizationRepository(db_session)

    # 1. Create & Save
    org = Organization(
        id="org-test-1",
        name="Test Corp",
        slug="test-corp",
    )
    saved = repo.save(org)
    assert saved.id == "org-test-1"
    assert saved.name == "Test Corp"
    assert saved.slug == "test-corp"

    # 2. Get by ID & Slug
    fetched_by_id = repo.get_by_id("org-test-1")
    assert fetched_by_id is not None
    assert fetched_by_id.name == "Test Corp"

    fetched_by_slug = repo.get_by_slug("test-corp")
    assert fetched_by_slug is not None
    assert fetched_by_slug.id == "org-test-1"

    # 3. Update
    fetched_by_id.update(name="Updated Test Corp")
    updated = repo.save(fetched_by_id)
    assert updated.name == "Updated Test Corp"

    # 4. List
    items, total = repo.list_all(page=1, page_size=10)
    assert total >= 1
    assert any(i.id == "org-test-1" for i in items)

    # 5. Delete
    deleted = repo.delete("org-test-1")
    assert deleted is True
    assert repo.get_by_id("org-test-1") is None
