"""Filter and pagination value object for domain repositories.

Defines standardized parameters for filtering, search, sorting, and pagination.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FilterParams:
    """Standardized parameter object for query filtering, sorting, and pagination.

    Attributes
    ----------
    page : int
        Page number (1-based index).
    page_size : int
        Maximum items per page.
    name : str | None
        Optional substring or exact match filter for entity name/title.
    owner_id : str | None
        Optional filter for owner user ID.
    created_at_from : datetime | None
        Optional filter for minimum creation timestamp.
    created_at_to : datetime | None
        Optional filter for maximum creation timestamp.
    updated_at_from : datetime | None
        Optional filter for minimum update timestamp.
    updated_at_to : datetime | None
        Optional filter for maximum update timestamp.
    is_active : bool | None
        Optional filter for entity active status.
    search : str | None
        Optional keyword search filter across name and description fields.
    sort_by : str
        Field name to sort by (e.g., 'created_at', 'updated_at', 'name').
    sort_order : str
        Sort direction: 'asc' or 'desc'.
    """

    page: int = 1
    page_size: int = 20
    name: str | None = None
    owner_id: str | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None
    dataset_id: str | None = None
    report_type: str | None = None
    is_public: bool | None = None
    is_active: bool | None = None
    search: str | None = None
    sort_by: str = "created_at"
    sort_order: str = "desc"

    def __post_init__(self) -> None:
        """Validate range bounds."""
        if self.page < 1:
            object.__setattr__(self, "page", 1)
        if self.page_size < 1:
            object.__setattr__(self, "page_size", 20)
        elif self.page_size > 100:
            object.__setattr__(self, "page_size", 100)
        if self.sort_order.lower() not in ("asc", "desc"):
            object.__setattr__(self, "sort_order", "desc")
