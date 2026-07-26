"""Dataset repository port interface.

Defines the contract for dataset persistence, query filtering, and retrieval.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.dataset import Dataset
from app.domain.value_objects.filter_params import FilterParams


@runtime_checkable
class IDatasetRepository(Protocol):
    """Port interface for persisting and fetching Dataset entities."""

    def get_by_id(self, dataset_id: str) -> Dataset | None:
        """Fetch a Dataset by its unique ID."""
        ...

    def save(self, dataset: Dataset) -> Dataset:
        """Persist a new Dataset or update an existing one."""
        ...

    def delete(self, dataset_id: str) -> bool:
        """Permanently remove a Dataset from persistence."""
        ...

    def list(self, params: FilterParams) -> tuple[list[Dataset], int]:
        """Fetch a paginated/filtered list of Datasets with total count."""
        ...
