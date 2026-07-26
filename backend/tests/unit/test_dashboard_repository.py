"""Comprehensive unit tests for SQLAlchemyDashboardRepository."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.value_objects.filter_params import FilterParams
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import UserModel
from app.infrastructure.repositories.dashboard_repository import (
    SQLAlchemyDashboardRepository,
)
from app.infrastructure.repositories.dataset_repository import (
    SQLAlchemyDatasetRepository,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    """In-memory SQLite session with owner user and test dataset seeded."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    now = datetime.now(UTC)
    user = UserModel(
        id="usr-repo-1",
        email="repo-owner@nexusbi.io",
        full_name="Repo Owner",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)

    ds_repo = SQLAlchemyDatasetRepository(session)
    ds1 = Dataset(
        id="ds-repo-1",
        name="Dataset 1",
        source_type="postgres",
        query_or_table="tbl1",
        owner_id="usr-repo-1",
    )
    ds2 = Dataset(
        id="ds-repo-2",
        name="Dataset 2",
        source_type="snowflake",
        query_or_table="tbl2",
        owner_id="usr-repo-1",
    )
    ds_repo.save(ds1)
    ds_repo.save(ds2)

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


def test_dashboard_repository_save_get_delete(db_session: Session) -> None:
    """Test saving, retrieving, updating, and deleting a dashboard."""
    repo = SQLAlchemyDashboardRepository(db_session)
    now = datetime.now(UTC)

    dashboard = Dashboard(
        id="dash-repo-01",
        name="Main Overview",
        owner_id="usr-repo-1",
        dataset_id="ds-repo-1",
        description="Main metrics",
        layout_json={"widgets": [1, 2]},
        is_public=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    # Save
    saved = repo.save(dashboard)
    assert saved.id == "dash-repo-01"

    # Get
    fetched = repo.get_by_id("dash-repo-01")
    assert fetched is not None
    assert fetched.name == "Main Overview"
    assert fetched.dataset_id == "ds-repo-1"
    assert fetched.layout_json == {"widgets": [1, 2]}
    assert fetched.is_public is True

    # Update
    dashboard.update(name="Updated Overview", dataset_id="ds-repo-2", is_public=False)
    repo.save(dashboard)

    updated_fetch = repo.get_by_id("dash-repo-01")
    assert updated_fetch is not None
    assert updated_fetch.name == "Updated Overview"
    assert updated_fetch.dataset_id == "ds-repo-2"
    assert updated_fetch.is_public is False

    # Delete
    assert repo.delete("dash-repo-01") is True
    assert repo.get_by_id("dash-repo-01") is None
    assert repo.delete("non-existent-id") is False


def test_dashboard_repository_list_filtering_and_sorting(
    db_session: Session,
) -> None:
    """Test listing dashboards with filters and sorting."""
    repo = SQLAlchemyDashboardRepository(db_session)
    now = datetime.now(UTC)

    d1 = Dashboard(
        id="dash-1",
        name="Alpha Dashboard",
        owner_id="usr-repo-1",
        dataset_id="ds-repo-1",
        description="First dashboard",
        is_public=True,
        is_active=True,
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2),
    )
    d2 = Dashboard(
        id="dash-2",
        name="Beta Dashboard",
        owner_id="usr-repo-1",
        dataset_id="ds-repo-2",
        description="Second dashboard",
        is_public=False,
        is_active=False,
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=1),
    )
    repo.save(d1)
    repo.save(d2)

    # Filter by name
    items, total = repo.list(FilterParams(name="Alpha"))
    assert total == 1
    assert items[0].id == "dash-1"

    # Filter by dataset_id
    items, total = repo.list(FilterParams(dataset_id="ds-repo-2"))
    assert total == 1
    assert items[0].id == "dash-2"

    # Filter by active status
    items, total = repo.list(FilterParams(is_active=False))
    assert total == 1
    assert items[0].id == "dash-2"

    # Filter by public status
    items, total = repo.list(FilterParams(is_public=True))
    assert total == 1
    assert items[0].id == "dash-1"

    # Keyword search
    items, total = repo.list(FilterParams(search="Second"))
    assert total == 1
    assert items[0].id == "dash-2"

    # Sorting by name asc
    items, total = repo.list(FilterParams(sort_by="name", sort_order="asc"))
    assert total == 2
    assert items[0].id == "dash-1"
    assert items[1].id == "dash-2"
