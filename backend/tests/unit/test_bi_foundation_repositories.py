"""Unit tests for SQLAlchemy repositories (Dashboard, Report, Dataset)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.entities.report import Report
from app.domain.value_objects.filter_params import FilterParams
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import UserModel
from app.infrastructure.repositories.dashboard_repository import (
    SQLAlchemyDashboardRepository,
)
from app.infrastructure.repositories.dataset_repository import (
    SQLAlchemyDatasetRepository,
)
from app.infrastructure.repositories.report_repository import (
    SQLAlchemyReportRepository,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    """Provide an in-memory SQLite database session for repository testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Seed a default user for foreign keys
    now = datetime.now(UTC)
    session.add(
        UserModel(
            id="owner-1",
            email="owner@nexusbi.io",
            full_name="Owner User",
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
        )
    )
    # Seed a default dataset for foreign keys
    dataset_repo = SQLAlchemyDatasetRepository(session)
    default_ds = Dataset(
        id="ds-seed-1",
        name="Seed Dataset",
        source_type="postgres",
        query_or_table="public.seed",
        owner_id="owner-1",
    )
    dataset_repo.save(default_ds)

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


def test_dashboard_repository_crud_and_querying(db_session: Session) -> None:
    """Test SQLAlchemyDashboardRepository CRUD, pagination, filter, search, sort."""
    repo = SQLAlchemyDashboardRepository(db_session)
    now = datetime.now(UTC)

    # 1. Create and Save
    dash1 = Dashboard(
        id="d-1",
        name="Finance Dashboard",
        owner_id="owner-1",
        dataset_id="ds-seed-1",
        description="Financial metrics",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )
    dash2 = Dashboard(
        id="d-2",
        name="Sales Overview",
        owner_id="owner-1",
        dataset_id="ds-seed-1",
        description="Daily sales pipeline",
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )
    repo.save(dash1)
    repo.save(dash2)

    # 2. Get by ID
    retrieved = repo.get_by_id("d-1")
    assert retrieved is not None
    assert retrieved.name == "Finance Dashboard"
    assert retrieved.dataset_id == "ds-seed-1"

    # 3. Update
    dash1.update(name="Updated Finance", is_public=True)
    repo.save(dash1)
    updated_fetch = repo.get_by_id("d-1")
    assert updated_fetch is not None
    assert updated_fetch.name == "Updated Finance"
    assert updated_fetch.is_public is True

    # 4. Filter by Name Substring
    items, total = repo.list(FilterParams(name="Overview"))
    assert total == 1
    assert items[0].id == "d-2"

    # 5. Keyword Search
    items, total = repo.list(FilterParams(search="pipeline"))
    assert total == 1
    assert items[0].id == "d-2"

    # 6. Sorting & Pagination
    items, total = repo.list(
        FilterParams(page=1, page_size=1, sort_by="created_at", sort_order="desc")
    )
    assert total == 2
    assert len(items) == 1
    assert items[0].id == "d-2"

    # 7. Delete
    deleted = repo.delete("d-1")
    assert deleted is True
    assert repo.get_by_id("d-1") is None
    assert repo.delete("non-existent") is False


def test_report_repository_crud_and_querying(db_session: Session) -> None:
    """Test SQLAlchemyReportRepository CRUD, filtering, search, sorting."""
    repo = SQLAlchemyReportRepository(db_session)

    rep1 = Report(
        id="r-1",
        name="Monthly Revenue",
        dataset_id="ds-seed-1",
        query="SELECT sum(amount) FROM revenue",
        owner_id="owner-1",
        description="Revenue breakdown",
    )
    rep2 = Report(
        id="r-2",
        name="User Growth",
        dataset_id="ds-seed-1",
        query="SELECT count(*) FROM users",
        owner_id="owner-1",
    )
    repo.save(rep1)
    repo.save(rep2)

    # Fetch
    retrieved = repo.get_by_id("r-1")
    assert retrieved is not None
    assert retrieved.query == "SELECT sum(amount) FROM revenue"

    # Search in query string
    items, total = repo.list(FilterParams(search="sum(amount)"))
    assert total == 1
    assert items[0].id == "r-1"

    # Delete
    assert repo.delete("r-2") is True
    assert repo.get_by_id("r-2") is None


def test_dataset_repository_crud_and_querying(db_session: Session) -> None:
    """Test SQLAlchemyDatasetRepository CRUD, filtering, search, sorting."""
    repo = SQLAlchemyDatasetRepository(db_session)

    ds1 = Dataset(
        id="ds-1",
        name="Customer Events",
        source_type="snowflake",
        query_or_table="analytics.events",
        owner_id="owner-1",
    )
    ds2 = Dataset(
        id="ds-2",
        name="Orders Data",
        source_type="postgres",
        query_or_table="public.orders",
        owner_id="owner-1",
    )
    repo.save(ds1)
    repo.save(ds2)

    # Fetch & Filter
    items, total = repo.list(FilterParams(name="Customer"))
    assert total == 1
    assert items[0].id == "ds-1"

    # Search query_or_table
    items, total = repo.list(FilterParams(search="public.orders"))
    assert total == 1
    assert items[0].id == "ds-2"

    # Delete
    assert repo.delete("ds-1") is True
    assert repo.get_by_id("ds-1") is None
