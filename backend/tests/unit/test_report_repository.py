"""Comprehensive unit tests for SQLAlchemyReportRepository."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.dataset import Dataset
from app.domain.entities.report import Report
from app.domain.value_objects.filter_params import FilterParams
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import UserModel
from app.infrastructure.repositories.dataset_repository import (
    SQLAlchemyDatasetRepository,
)
from app.infrastructure.repositories.report_repository import (
    SQLAlchemyReportRepository,
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


def test_report_repository_save_get_delete(db_session: Session) -> None:
    """Test saving, retrieving, updating, and deleting a report."""
    repo = SQLAlchemyReportRepository(db_session)
    now = datetime.now(UTC)

    report = Report(
        id="rep-repo-01",
        name="Main Financial Summary",
        dataset_id="ds-repo-1",
        owner_id="usr-repo-1",
        report_type="summary",
        output_format="pdf",
        description="Main financial breakdown",
        schedule="0 0 * * *",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    # Save
    saved = repo.save(report)
    assert saved.id == "rep-repo-01"

    # Get
    fetched = repo.get_by_id("rep-repo-01")
    assert fetched is not None
    assert fetched.name == "Main Financial Summary"
    assert fetched.dataset_id == "ds-repo-1"
    assert fetched.report_type == "summary"
    assert fetched.output_format == "pdf"
    assert fetched.schedule == "0 0 * * *"
    assert fetched.is_active is True

    # Update
    report.update(name="Updated Summary", dataset_id="ds-repo-2", output_format="json")
    repo.save(report)

    updated_fetch = repo.get_by_id("rep-repo-01")
    assert updated_fetch is not None
    assert updated_fetch.name == "Updated Summary"
    assert updated_fetch.dataset_id == "ds-repo-2"
    assert updated_fetch.output_format == "json"

    # Delete
    assert repo.delete("rep-repo-01") is True
    assert repo.get_by_id("rep-repo-01") is None
    assert repo.delete("non-existent-id") is False


def test_report_repository_list_filtering_and_sorting(
    db_session: Session,
) -> None:
    """Test listing reports with filters, search, and sorting."""
    repo = SQLAlchemyReportRepository(db_session)
    now = datetime.now(UTC)

    r1 = Report(
        id="rep-1",
        name="Alpha Report",
        dataset_id="ds-repo-1",
        owner_id="usr-repo-1",
        report_type="tabular",
        output_format="csv",
        description="Alpha description",
        is_active=True,
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2),
    )
    r2 = Report(
        id="rep-2",
        name="Beta Report",
        dataset_id="ds-repo-2",
        owner_id="usr-repo-1",
        report_type="chart",
        output_format="json",
        description="Beta description",
        is_active=False,
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=1),
    )
    repo.save(r1)
    repo.save(r2)

    # Filter by name
    items, total = repo.list(FilterParams(name="Alpha"))
    assert total == 1
    assert items[0].id == "rep-1"

    # Filter by dataset_id
    items, total = repo.list(FilterParams(dataset_id="ds-repo-2"))
    assert total == 1
    assert items[0].id == "rep-2"

    # Filter by report_type
    items, total = repo.list(FilterParams(report_type="chart"))
    assert total == 1
    assert items[0].id == "rep-2"

    # Filter by active status
    items, total = repo.list(FilterParams(is_active=False))
    assert total == 1
    assert items[0].id == "rep-2"

    # Keyword search
    items, total = repo.list(FilterParams(search="Alpha"))
    assert total == 1
    assert items[0].id == "rep-1"

    # Sorting by name asc
    items, total = repo.list(FilterParams(sort_by="name", sort_order="asc"))
    assert total == 2
    assert items[0].id == "rep-1"
    assert items[1].id == "rep-2"
