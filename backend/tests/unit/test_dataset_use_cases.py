"""Comprehensive unit tests for Dataset application use cases.

Each use case is tested in isolation with mock repositories, covering
happy paths, error scenarios, and DTO mapping correctness.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.dataset_dto import (
    CreateDatasetDTO,
    UpdateDatasetDTO,
)
from app.application.use_cases.create_dataset import CreateDatasetUseCase
from app.application.use_cases.delete_dataset import DeleteDatasetUseCase
from app.application.use_cases.get_dataset import GetDatasetUseCase
from app.application.use_cases.list_datasets import ListDatasetsUseCase
from app.application.use_cases.update_dataset import UpdateDatasetUseCase
from app.core.exceptions import EntityNotFoundError
from app.domain.entities.dataset import Dataset
from app.domain.value_objects.filter_params import FilterParams


def _make_dataset(
    id: str = "ds-1",
    name: str = "Orders",
    source_type: str = "postgres",
    query_or_table: str = "public.orders",
    owner_id: str = "user-1",
    **kwargs: object,
) -> Dataset:
    """Factory for creating Dataset domain entities for testing."""
    return Dataset(
        id=id,
        name=name,
        source_type=source_type,
        query_or_table=query_or_table,
        owner_id=owner_id,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# CreateDatasetUseCase
# ---------------------------------------------------------------------------


class TestCreateDatasetUseCase:
    """Tests for the CreateDatasetUseCase."""

    def test_creates_and_returns_dataset_dto(self) -> None:
        """Use case creates a dataset entity and returns a DTO."""
        repo = MagicMock()
        dataset = _make_dataset()
        repo.save.return_value = dataset

        uc = CreateDatasetUseCase(dataset_repository=repo)
        dto = uc.execute(
            CreateDatasetDTO(
                name="Orders",
                source_type="postgres",
                query_or_table="public.orders",
            ),
            owner_id="user-1",
        )

        assert dto.name == "Orders"
        assert dto.source_type == "postgres"
        assert dto.query_or_table == "public.orders"
        assert dto.owner_id == "user-1"
        assert dto.is_active is True
        repo.save.assert_called_once()

    def test_uuid_is_generated(self) -> None:
        """Each invocation generates a unique UUID for the dataset."""
        repo = MagicMock()
        dataset = _make_dataset()
        repo.save.return_value = dataset

        uc = CreateDatasetUseCase(dataset_repository=repo)
        uc.execute(
            CreateDatasetDTO(name="Test", source_type="csv", query_or_table="data.csv"),
            owner_id="u-1",
        )

        saved_entity = repo.save.call_args[0][0]
        assert saved_entity.id is not None
        assert len(saved_entity.id) == 36  # UUID format

    def test_optional_fields_passed_through(self) -> None:
        """Description, schema_metadata, and is_active are forwarded."""
        repo = MagicMock()
        dataset = _make_dataset(
            description="Test desc",
            schema_metadata={"col": "int"},
            is_active=False,
        )
        repo.save.return_value = dataset

        uc = CreateDatasetUseCase(dataset_repository=repo)
        dto = uc.execute(
            CreateDatasetDTO(
                name="Orders",
                source_type="pg",
                query_or_table="tbl",
                description="Test desc",
                schema_metadata={"col": "int"},
                is_active=False,
            ),
            owner_id="user-1",
        )

        assert dto.description == "Test desc"
        assert dto.schema_metadata == {"col": "int"}
        assert dto.is_active is False

    def test_created_at_and_updated_at_in_response(self) -> None:
        """Response DTO contains timestamp fields."""
        repo = MagicMock()
        now = datetime.now(UTC)
        dataset = _make_dataset(created_at=now, updated_at=now)
        repo.save.return_value = dataset

        uc = CreateDatasetUseCase(dataset_repository=repo)
        dto = uc.execute(
            CreateDatasetDTO(name="Test", source_type="pg", query_or_table="t"),
            owner_id="u-1",
        )

        assert dto.created_at == now
        assert dto.updated_at == now


# ---------------------------------------------------------------------------
# GetDatasetUseCase
# ---------------------------------------------------------------------------


class TestGetDatasetUseCase:
    """Tests for the GetDatasetUseCase."""

    def test_returns_dto_for_existing_dataset(self) -> None:
        """Use case returns a DatasetDTO when dataset exists."""
        repo = MagicMock()
        dataset = _make_dataset()
        repo.get_by_id.return_value = dataset

        uc = GetDatasetUseCase(dataset_repository=repo)
        dto = uc.execute("ds-1")

        assert dto.id == "ds-1"
        assert dto.name == "Orders"
        repo.get_by_id.assert_called_once_with("ds-1")

    def test_raises_not_found_for_missing_dataset(self) -> None:
        """Use case raises EntityNotFoundError when dataset doesn't exist."""
        repo = MagicMock()
        repo.get_by_id.return_value = None

        uc = GetDatasetUseCase(dataset_repository=repo)
        with pytest.raises(EntityNotFoundError) as exc_info:
            uc.execute("nonexistent")

        assert "Dataset" in exc_info.value.message
        assert "nonexistent" in (exc_info.value.detail or "")

    def test_dto_maps_all_fields(self) -> None:
        """All domain entity fields are mapped to the DTO."""
        repo = MagicMock()
        now = datetime.now(UTC)
        dataset = _make_dataset(
            description="Full desc",
            schema_metadata={"x": 1},
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        repo.get_by_id.return_value = dataset

        uc = GetDatasetUseCase(dataset_repository=repo)
        dto = uc.execute("ds-1")

        assert dto.description == "Full desc"
        assert dto.schema_metadata == {"x": 1}
        assert dto.is_active is False
        assert dto.created_at == now
        assert dto.updated_at == now


# ---------------------------------------------------------------------------
# UpdateDatasetUseCase
# ---------------------------------------------------------------------------


class TestUpdateDatasetUseCase:
    """Tests for the UpdateDatasetUseCase."""

    def test_updates_and_returns_dto(self) -> None:
        """Use case updates the entity and returns the saved DTO."""
        repo = MagicMock()
        dataset = _make_dataset()
        repo.get_by_id.return_value = dataset
        repo.save.return_value = dataset

        uc = UpdateDatasetUseCase(dataset_repository=repo)
        dto = uc.execute("ds-1", UpdateDatasetDTO(name="Updated Name"))

        assert dto.name == "Updated Name"
        repo.get_by_id.assert_called_once_with("ds-1")
        repo.save.assert_called_once()

    def test_raises_not_found_for_missing_dataset(self) -> None:
        """Use case raises EntityNotFoundError when dataset doesn't exist."""
        repo = MagicMock()
        repo.get_by_id.return_value = None

        uc = UpdateDatasetUseCase(dataset_repository=repo)
        with pytest.raises(EntityNotFoundError):
            uc.execute("nonexistent", UpdateDatasetDTO(name="X"))

    def test_partial_update_preserves_unset_fields(self) -> None:
        """Only provided fields are updated; others remain unchanged."""
        repo = MagicMock()
        dataset = _make_dataset(description="Original desc")
        repo.get_by_id.return_value = dataset
        repo.save.return_value = dataset

        uc = UpdateDatasetUseCase(dataset_repository=repo)
        dto = uc.execute("ds-1", UpdateDatasetDTO(is_active=False))

        assert dto.description == "Original desc"
        assert dto.is_active is False

    def test_update_multiple_fields(self) -> None:
        """Multiple fields can be updated simultaneously."""
        repo = MagicMock()
        dataset = _make_dataset()
        repo.get_by_id.return_value = dataset
        repo.save.return_value = dataset

        uc = UpdateDatasetUseCase(dataset_repository=repo)
        dto = uc.execute(
            "ds-1",
            UpdateDatasetDTO(
                name="New Name",
                source_type="snowflake",
                query_or_table="events",
                description="New desc",
                is_active=False,
            ),
        )

        assert dto.name == "New Name"
        assert dto.source_type == "snowflake"


# ---------------------------------------------------------------------------
# DeleteDatasetUseCase
# ---------------------------------------------------------------------------


class TestDeleteDatasetUseCase:
    """Tests for the DeleteDatasetUseCase."""

    def test_deletes_existing_dataset(self) -> None:
        """Use case successfully deletes an existing dataset."""
        repo = MagicMock()
        repo.delete.return_value = True

        uc = DeleteDatasetUseCase(dataset_repository=repo)
        uc.execute("ds-1")  # Should not raise

        repo.delete.assert_called_once_with("ds-1")

    def test_raises_not_found_for_missing_dataset(self) -> None:
        """Use case raises EntityNotFoundError when dataset doesn't exist."""
        repo = MagicMock()
        repo.delete.return_value = False

        uc = DeleteDatasetUseCase(dataset_repository=repo)
        with pytest.raises(EntityNotFoundError):
            uc.execute("nonexistent")


# ---------------------------------------------------------------------------
# ListDatasetsUseCase
# ---------------------------------------------------------------------------


class TestListDatasetsUseCase:
    """Tests for the ListDatasetsUseCase."""

    def test_returns_paginated_response(self) -> None:
        """Use case returns a PaginatedResponse with correct metadata."""
        repo = MagicMock()
        datasets = [_make_dataset(id=f"ds-{i}") for i in range(3)]
        repo.list.return_value = (datasets, 3)

        uc = ListDatasetsUseCase(dataset_repository=repo)
        result = uc.execute(FilterParams(page=1, page_size=10))

        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1
        assert len(result.items) == 3

    def test_empty_results(self) -> None:
        """Use case handles empty result set correctly."""
        repo = MagicMock()
        repo.list.return_value = ([], 0)

        uc = ListDatasetsUseCase(dataset_repository=repo)
        result = uc.execute(FilterParams())

        assert result.total == 0
        assert result.total_pages == 0
        assert result.items == []

    def test_pagination_math_multiple_pages(self) -> None:
        """total_pages is correctly calculated for multi-page results."""
        repo = MagicMock()
        datasets = [_make_dataset(id=f"ds-{i}") for i in range(5)]
        repo.list.return_value = (datasets, 23)

        uc = ListDatasetsUseCase(dataset_repository=repo)
        result = uc.execute(FilterParams(page=1, page_size=5))

        assert result.total == 23
        assert result.total_pages == 5  # ceil(23/5) = 5

    def test_params_passed_to_repository(self) -> None:
        """FilterParams are forwarded to the repository unchanged."""
        repo = MagicMock()
        repo.list.return_value = ([], 0)

        params = FilterParams(
            page=2,
            page_size=10,
            name="test",
            owner_id="u-1",
            is_active=True,
            sort_by="name",
            sort_order="asc",
        )

        uc = ListDatasetsUseCase(dataset_repository=repo)
        uc.execute(params)

        repo.list.assert_called_once_with(params)

    def test_dtos_contain_all_fields(self) -> None:
        """Each item DTO in the response maps all dataset fields."""
        repo = MagicMock()
        now = datetime.now(UTC)
        dataset = _make_dataset(
            description="Desc",
            schema_metadata={"k": "v"},
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        repo.list.return_value = ([dataset], 1)

        uc = ListDatasetsUseCase(dataset_repository=repo)
        result = uc.execute(FilterParams())

        item = result.items[0]
        assert item.id == "ds-1"
        assert item.description == "Desc"
        assert item.schema_metadata == {"k": "v"}
        assert item.is_active is False
        assert item.created_at == now
        assert item.updated_at == now
