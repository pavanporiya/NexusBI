"""Comprehensive unit tests for the SQLAlchemy Dataset repository.

Uses an in-memory SQLite database to exercise CRUD, filtering, search,
sorting, and pagination in the concrete repository implementation.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.dataset import Dataset
from app.domain.value_objects.filter_params import FilterParams
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import UserModel
from app.infrastructure.repositories.dataset_repository import (
    SQLAlchemyDatasetRepository,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session() -> Generator[Session]:
    """Provide an in-memory SQLite database session for repository testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    now = datetime.now(UTC)
    user = UserModel(
        id="owner-1",
        email="owner@nexusbi.io",
        full_name="Owner User",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    user2 = UserModel(
        id="owner-2",
        email="owner2@nexusbi.io",
        full_name="Second Owner",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    session.add_all([user, user2])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def repo(db_session: Session) -> SQLAlchemyDatasetRepository:
    """Provide a dataset repository backed by the in-memory DB."""
    return SQLAlchemyDatasetRepository(db_session)


def _make_dataset(
    id: str = "ds-1",
    name: str = "Orders",
    source_type: str = "postgres",
    query_or_table: str = "public.orders",
    owner_id: str = "owner-1",
    description: str | None = None,
    is_active: bool = True,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Dataset:
    """Factory for creating Dataset domain entities."""
    now = datetime.now(UTC)
    return Dataset(
        id=id,
        name=name,
        source_type=source_type,
        query_or_table=query_or_table,
        owner_id=owner_id,
        description=description,
        is_active=is_active,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------


class TestDatasetRepositoryCRUD:
    """Tests for basic CRUD operations."""

    def test_save_and_get_by_id(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Save a dataset and retrieve it by ID."""
        ds = _make_dataset()
        saved = repo.save(ds)
        assert saved.id == "ds-1"
        assert saved.name == "Orders"

        fetched = repo.get_by_id("ds-1")
        assert fetched is not None
        assert fetched.id == "ds-1"
        assert fetched.name == "Orders"
        assert fetched.source_type == "postgres"
        assert fetched.query_or_table == "public.orders"
        assert fetched.owner_id == "owner-1"

    def test_get_nonexistent_returns_none(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Getting a non-existent ID returns None."""
        assert repo.get_by_id("nonexistent-id") is None

    def test_save_update_existing(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Save an entity, then save again to update it."""
        ds = _make_dataset()
        repo.save(ds)

        ds.update(name="Updated Orders", description="Updated desc")
        saved = repo.save(ds)
        assert saved.name == "Updated Orders"
        assert saved.description == "Updated desc"

        fetched = repo.get_by_id("ds-1")
        assert fetched is not None
        assert fetched.name == "Updated Orders"
        assert fetched.description == "Updated desc"

    def test_delete_existing(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Delete an existing dataset returns True."""
        repo.save(_make_dataset())
        assert repo.delete("ds-1") is True
        assert repo.get_by_id("ds-1") is None

    def test_delete_nonexistent_returns_false(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Deleting a non-existent dataset returns False."""
        assert repo.delete("no-such-id") is False

    def test_save_preserves_all_fields(self, repo: SQLAlchemyDatasetRepository) -> None:
        """All entity fields round-trip through save/get correctly."""
        now = datetime.now(UTC)
        ds = _make_dataset(
            description="Full description",
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        ds_meta = {"columns": [{"name": "id", "type": "int"}]}
        ds.update(schema_metadata=ds_meta)
        repo.save(ds)

        fetched = repo.get_by_id("ds-1")
        assert fetched is not None
        assert fetched.description == "Full description"
        assert fetched.is_active is False
        assert fetched.schema_metadata == ds_meta


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


class TestDatasetRepositoryFiltering:
    """Tests for list() filtering capabilities."""

    def _seed(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Seed multiple datasets for filtering tests."""
        now = datetime.now(UTC)
        datasets = [
            _make_dataset(
                id="ds-1",
                name="Customer Events",
                source_type="snowflake",
                query_or_table="analytics.events",
                owner_id="owner-1",
                description="Event tracking data",
                is_active=True,
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=2),
            ),
            _make_dataset(
                id="ds-2",
                name="Orders Data",
                source_type="postgres",
                query_or_table="public.orders",
                owner_id="owner-1",
                description="Retail orders",
                is_active=True,
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=1),
            ),
            _make_dataset(
                id="ds-3",
                name="Archived Data",
                source_type="csv",
                query_or_table="archive.csv",
                owner_id="owner-2",
                description="Old archived data",
                is_active=False,
                created_at=now - timedelta(days=1),
                updated_at=now,
            ),
        ]
        for ds in datasets:
            repo.save(ds)

    def test_filter_by_name_substring(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Filter by name performs case-insensitive substring matching."""
        self._seed(repo)
        items, total = repo.list(FilterParams(name="customer"))
        assert total == 1
        assert items[0].id == "ds-1"

    def test_filter_by_owner_id(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Filter by owner_id returns only datasets owned by that user."""
        self._seed(repo)
        items, total = repo.list(FilterParams(owner_id="owner-2"))
        assert total == 1
        assert items[0].id == "ds-3"

    def test_filter_by_is_active_true(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Filter by is_active=True returns only active datasets."""
        self._seed(repo)
        items, total = repo.list(FilterParams(is_active=True))
        assert total == 2
        ids = {i.id for i in items}
        assert ids == {"ds-1", "ds-2"}

    def test_filter_by_is_active_false(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Filter by is_active=False returns only inactive datasets."""
        self._seed(repo)
        items, total = repo.list(FilterParams(is_active=False))
        assert total == 1
        assert items[0].id == "ds-3"

    def test_filter_by_is_active_none_returns_all(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Filter with is_active=None returns all datasets."""
        self._seed(repo)
        _items, total = repo.list(FilterParams(is_active=None))
        assert total == 3

    def test_filter_by_created_at_range(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Filter by created_at range narrows results."""
        self._seed(repo)
        now = datetime.now(UTC)
        items, total = repo.list(
            FilterParams(
                created_at_from=now - timedelta(days=2, hours=12),
                created_at_to=now - timedelta(hours=12),
            )
        )
        assert total == 2
        ids = {i.id for i in items}
        assert ids == {"ds-2", "ds-3"}

    def test_filter_by_updated_at_range(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Filter by updated_at range narrows results."""
        self._seed(repo)
        now = datetime.now(UTC)
        items, total = repo.list(
            FilterParams(
                updated_at_from=now - timedelta(hours=12),
            )
        )
        assert total == 1
        assert items[0].id == "ds-3"

    def test_combined_filters(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Multiple filters combine with AND logic."""
        self._seed(repo)
        items, total = repo.list(
            FilterParams(owner_id="owner-1", is_active=True, name="orders")
        )
        assert total == 1
        assert items[0].id == "ds-2"


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestDatasetRepositorySearch:
    """Tests for keyword search across name, description, query_or_table."""

    def _seed(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Seed datasets for search tests."""
        repo.save(
            _make_dataset(
                id="ds-s1",
                name="Sales Pipeline",
                description="Monthly sales funnel",
                query_or_table="sales.pipeline",
            )
        )
        repo.save(
            _make_dataset(
                id="ds-s2",
                name="Marketing Data",
                description="Campaign metrics",
                query_or_table="marketing.campaigns",
            )
        )

    def test_search_matches_name(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Search term matching name returns correct result."""
        self._seed(repo)
        items, total = repo.list(FilterParams(search="pipeline"))
        assert total == 1
        assert items[0].id == "ds-s1"

    def test_search_matches_description(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Search term matching description returns correct result."""
        self._seed(repo)
        items, total = repo.list(FilterParams(search="campaign"))
        assert total == 1
        assert items[0].id == "ds-s2"

    def test_search_matches_query_or_table(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Search term matching query_or_table returns correct result."""
        self._seed(repo)
        items, total = repo.list(FilterParams(search="marketing.campaigns"))
        assert total == 1
        assert items[0].id == "ds-s2"

    def test_search_no_match(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Search term with no match returns empty results."""
        self._seed(repo)
        items, total = repo.list(FilterParams(search="nonexistent"))
        assert total == 0
        assert items == []

    def test_search_case_insensitive(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Search is case-insensitive."""
        self._seed(repo)
        items, total = repo.list(FilterParams(search="PIPELINE"))
        assert total == 1
        assert items[0].id == "ds-s1"


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


class TestDatasetRepositorySorting:
    """Tests for sorting by name, created_at, and updated_at."""

    def _seed(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Seed datasets with distinct timestamps for sorting tests."""
        now = datetime.now(UTC)
        repo.save(
            _make_dataset(
                id="ds-a",
                name="Alpha",
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=3),
            )
        )
        repo.save(
            _make_dataset(
                id="ds-b",
                name="Charlie",
                created_at=now - timedelta(days=1),
                updated_at=now - timedelta(days=2),
            )
        )
        repo.save(
            _make_dataset(
                id="ds-c",
                name="Bravo",
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=1),
            )
        )

    def test_sort_by_name_asc(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Sorting by name ascending returns alphabetical order."""
        self._seed(repo)
        items, _ = repo.list(FilterParams(sort_by="name", sort_order="asc"))
        names = [i.name for i in items]
        assert names == ["Alpha", "Bravo", "Charlie"]

    def test_sort_by_name_desc(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Sorting by name descending returns reverse alphabetical order."""
        self._seed(repo)
        items, _ = repo.list(FilterParams(sort_by="name", sort_order="desc"))
        names = [i.name for i in items]
        assert names == ["Charlie", "Bravo", "Alpha"]

    def test_sort_by_created_at_asc(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Sorting by created_at ascending returns oldest first."""
        self._seed(repo)
        items, _ = repo.list(FilterParams(sort_by="created_at", sort_order="asc"))
        ids = [i.id for i in items]
        assert ids == ["ds-a", "ds-c", "ds-b"]

    def test_sort_by_created_at_desc(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Sorting by created_at descending returns newest first (default)."""
        self._seed(repo)
        items, _ = repo.list(FilterParams(sort_by="created_at", sort_order="desc"))
        ids = [i.id for i in items]
        assert ids == ["ds-b", "ds-c", "ds-a"]

    def test_sort_by_updated_at_asc(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Sorting by updated_at ascending returns least-recently-updated first."""
        self._seed(repo)
        items, _ = repo.list(FilterParams(sort_by="updated_at", sort_order="asc"))
        ids = [i.id for i in items]
        assert ids == ["ds-a", "ds-b", "ds-c"]

    def test_sort_by_updated_at_desc(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Sorting by updated_at descending returns most-recently-updated first."""
        self._seed(repo)
        items, _ = repo.list(FilterParams(sort_by="updated_at", sort_order="desc"))
        ids = [i.id for i in items]
        assert ids == ["ds-c", "ds-b", "ds-a"]

    def test_default_sort_is_created_at_desc(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Default sort order is created_at descending."""
        self._seed(repo)
        items, _ = repo.list(FilterParams())
        ids = [i.id for i in items]
        assert ids == ["ds-b", "ds-c", "ds-a"]


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestDatasetRepositoryPagination:
    """Tests for pagination behaviour."""

    def _seed(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Seed 5 datasets for pagination testing."""
        now = datetime.now(UTC)
        for i in range(1, 6):
            repo.save(
                _make_dataset(
                    id=f"ds-p{i}",
                    name=f"Dataset {i}",
                    created_at=now - timedelta(days=5 - i),
                    updated_at=now - timedelta(days=5 - i),
                )
            )

    def test_first_page(self, repo: SQLAlchemyDatasetRepository) -> None:
        """First page returns correct slice."""
        self._seed(repo)
        items, total = repo.list(
            FilterParams(page=1, page_size=2, sort_by="created_at", sort_order="asc")
        )
        assert total == 5
        assert len(items) == 2
        assert items[0].id == "ds-p1"
        assert items[1].id == "ds-p2"

    def test_second_page(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Second page returns correct slice."""
        self._seed(repo)
        items, total = repo.list(
            FilterParams(page=2, page_size=2, sort_by="created_at", sort_order="asc")
        )
        assert total == 5
        assert len(items) == 2
        assert items[0].id == "ds-p3"
        assert items[1].id == "ds-p4"

    def test_last_page_partial(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Last page may contain fewer items than page_size."""
        self._seed(repo)
        items, total = repo.list(
            FilterParams(page=3, page_size=2, sort_by="created_at", sort_order="asc")
        )
        assert total == 5
        assert len(items) == 1
        assert items[0].id == "ds-p5"

    def test_page_beyond_total_returns_empty(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Page beyond total returns empty items but correct total."""
        self._seed(repo)
        items, total = repo.list(FilterParams(page=100, page_size=10))
        assert total == 5
        assert items == []

    def test_large_page_size_returns_all(
        self, repo: SQLAlchemyDatasetRepository
    ) -> None:
        """Page size larger than total returns all items."""
        self._seed(repo)
        items, total = repo.list(FilterParams(page=1, page_size=100))
        assert total == 5
        assert len(items) == 5

    def test_empty_list(self, repo: SQLAlchemyDatasetRepository) -> None:
        """Listing with no data returns empty results."""
        items, total = repo.list(FilterParams())
        assert total == 0
        assert items == []
