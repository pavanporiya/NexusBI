"""Comprehensive unit tests for the Dataset domain entity.

Covers creation, invariant validation, update method, and timestamp mutation.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.entities.dataset import Dataset
from app.domain.enums import DatasetObjectType, DatasetSourceType
from app.domain.exceptions import DomainValidationError

# ---------------------------------------------------------------------------
# Construction & Invariant Validation
# ---------------------------------------------------------------------------


class TestDatasetCreation:
    """Tests for Dataset entity construction and invariant enforcement."""

    def test_valid_creation_with_all_fields(self) -> None:
        """Dataset initialises correctly with all explicit fields."""
        now = datetime.now(UTC)
        dataset = Dataset(
            id="ds-001",
            name="Sales Transactions",
            source_type="postgres",
            query_or_table="public.transactions",
            owner_id="user-1",
            description="Retail sales data",
            schema_metadata={"columns": ["id", "amount"]},
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        assert dataset.id == "ds-001"
        assert dataset.name == "Sales Transactions"
        assert dataset.source_type == DatasetSourceType.POSTGRES
        assert dataset.query_or_table == "public.transactions"
        assert dataset.object_type == DatasetObjectType.TABLE
        assert dataset.object_name == "public.transactions"
        assert dataset.owner_id == "user-1"
        assert dataset.description == "Retail sales data"
        assert dataset.schema_metadata == {"columns": ["id", "amount"]}
        assert dataset.is_active is False
        assert dataset.created_at == now
        assert dataset.updated_at == now

    def test_valid_creation_with_defaults(self) -> None:
        """Dataset applies sane defaults for optional fields."""
        dataset = Dataset(
            id="ds-002",
            name="Events",
            source_type="snowflake",
            query_or_table="analytics.events",
            owner_id="u-1",
        )
        assert dataset.description is None
        assert dataset.schema_metadata == {}
        assert dataset.is_active is True
        assert isinstance(dataset.created_at, datetime)
        assert isinstance(dataset.updated_at, datetime)

    def test_name_is_stripped_on_creation(self) -> None:
        """Leading and trailing whitespace is removed from name."""
        dataset = Dataset(
            id="ds-003",
            name="  Whitespace Name  ",
            source_type="csv",
            query_or_table="data.csv",
            owner_id="u-1",
        )
        assert dataset.name == "Whitespace Name"

    def test_source_type_is_stripped_on_creation(self) -> None:
        """Leading and trailing whitespace is removed from source_type."""
        dataset = Dataset(
            id="ds-004",
            name="Valid",
            source_type="  postgres  ",
            query_or_table="tbl",
            owner_id="u-1",
        )
        assert dataset.source_type == DatasetSourceType.POSTGRES

    def test_query_or_table_is_stripped_on_creation(self) -> None:
        """Leading and trailing whitespace is removed from query_or_table."""
        dataset = Dataset(
            id="ds-005",
            name="Valid",
            source_type="custom",
            query_or_table="  public.orders  ",
            owner_id="u-1",
        )
        assert dataset.query_or_table == "public.orders"

    def test_empty_name_raises_error(self) -> None:
        """Empty or whitespace-only name raises DomainValidationError."""
        msg = "Dataset name must not be empty"
        with pytest.raises(DomainValidationError, match=msg):
            Dataset(
                id="ds-x",
                name="",
                source_type="postgres",
                query_or_table="t",
                owner_id="u",
            )

    def test_whitespace_only_name_raises_error(self) -> None:
        """Whitespace-only name raises DomainValidationError."""
        msg = "Dataset name must not be empty"
        with pytest.raises(DomainValidationError, match=msg):
            Dataset(
                id="ds-x",
                name="   ",
                source_type="postgres",
                query_or_table="t",
                owner_id="u",
            )

    def test_empty_source_type_raises_error(self) -> None:
        """Empty source_type raises DomainValidationError."""
        with pytest.raises(
            DomainValidationError, match="Dataset source_type must not be empty"
        ):
            Dataset(
                id="ds-x",
                name="Valid",
                source_type="",
                query_or_table="t",
                owner_id="u",
            )

    def test_invalid_source_type_raises_error(self) -> None:
        """Invalid source_type raises DomainValidationError."""
        with pytest.raises(DomainValidationError, match="Invalid dataset source_type"):
            Dataset(
                id="ds-x",
                name="Valid",
                source_type="unknown_db",
                query_or_table="t",
                owner_id="u",
            )

    def test_empty_owner_id_raises_error(self) -> None:
        """Empty owner_id raises DomainValidationError."""
        with pytest.raises(
            DomainValidationError, match="Dataset owner_id must not be empty"
        ):
            Dataset(
                id="ds-x",
                name="Valid",
                source_type="postgres",
                query_or_table="t",
                owner_id="",
            )

    def test_table_object_type_rules(self) -> None:
        """TABLE requires object_name and forbids sql_query."""
        ds = Dataset(
            id="ds-t1",
            name="Table DS",
            source_type="postgres",
            object_type=DatasetObjectType.TABLE,
            object_name="users",
            owner_id="u1",
        )
        assert ds.object_type == DatasetObjectType.TABLE
        assert ds.object_name == "users"

        with pytest.raises(
            DomainValidationError, match="TABLE dataset requires non-empty object_name"
        ):
            Dataset(
                id="ds-t2",
                name="Table DS",
                source_type="postgres",
                object_type=DatasetObjectType.TABLE,
                object_name="",
                owner_id="u1",
            )

        with pytest.raises(
            DomainValidationError, match="TABLE dataset must not contain sql_query"
        ):
            Dataset(
                id="ds-t3",
                name="Table DS",
                source_type="postgres",
                object_type=DatasetObjectType.TABLE,
                object_name="users",
                sql_query="SELECT 1",
                owner_id="u1",
            )

    def test_view_object_type_rules(self) -> None:
        """VIEW requires object_name."""
        ds = Dataset(
            id="ds-v1",
            name="View DS",
            source_type="postgres",
            object_type=DatasetObjectType.VIEW,
            object_name="v_users",
            owner_id="u1",
        )
        assert ds.object_type == DatasetObjectType.VIEW
        assert ds.object_name == "v_users"

        with pytest.raises(
            DomainValidationError, match="VIEW dataset requires non-empty object_name"
        ):
            Dataset(
                id="ds-v2",
                name="View DS",
                source_type="postgres",
                object_type=DatasetObjectType.VIEW,
                object_name="",
                owner_id="u1",
            )

    def test_query_object_type_rules(self) -> None:
        """QUERY requires sql_query."""
        ds = Dataset(
            id="ds-q1",
            name="Query DS",
            source_type="snowflake",
            object_type=DatasetObjectType.QUERY,
            sql_query="SELECT * FROM events",
            owner_id="u1",
        )
        assert ds.object_type == DatasetObjectType.QUERY
        assert ds.sql_query == "SELECT * FROM events"

        with pytest.raises(
            DomainValidationError, match="QUERY dataset requires non-empty sql_query"
        ):
            Dataset(
                id="ds-q2",
                name="Query DS",
                source_type="snowflake",
                object_type=DatasetObjectType.QUERY,
                sql_query="",
                owner_id="u1",
            )


# ---------------------------------------------------------------------------
# Update Method
# ---------------------------------------------------------------------------


class TestDatasetUpdate:
    """Tests for the Dataset.update() method."""

    def _make_dataset(self) -> Dataset:
        """Create a standard Dataset for update testing."""
        return Dataset(
            id="ds-u1",
            name="Original",
            source_type="postgres",
            query_or_table="public.orders",
            owner_id="user-1",
            description="Original description",
            schema_metadata={"col": "val"},
            is_active=True,
        )

    def test_update_name(self) -> None:
        """Updating name strips whitespace and sets updated_at."""
        ds = self._make_dataset()
        old_ts = ds.updated_at
        ds.update(name="  New Name  ")
        assert ds.name == "New Name"
        assert ds.updated_at >= old_ts

    def test_update_description(self) -> None:
        """Updating description sets new value."""
        ds = self._make_dataset()
        ds.update(description="Updated desc")
        assert ds.description == "Updated desc"

    def test_update_source_type(self) -> None:
        """Updating source_type strips and validates."""
        ds = self._make_dataset()
        ds.update(source_type="  snowflake  ")
        assert ds.source_type == DatasetSourceType.SNOWFLAKE

    def test_update_query_or_table(self) -> None:
        """Updating query_or_table strips and validates."""
        ds = self._make_dataset()
        ds.update(query_or_table="  analytics.events  ")
        assert ds.query_or_table == "analytics.events"

    def test_update_schema_metadata(self) -> None:
        """Updating schema_metadata replaces entire dict."""
        ds = self._make_dataset()
        new_meta = {"columns": ["a", "b"], "types": {"a": "int"}}
        ds.update(schema_metadata=new_meta)
        assert ds.schema_metadata == new_meta

    def test_update_is_active(self) -> None:
        """Updating is_active toggles the flag."""
        ds = self._make_dataset()
        assert ds.is_active is True
        ds.update(is_active=False)
        assert ds.is_active is False
        ds.update(is_active=True)
        assert ds.is_active is True
