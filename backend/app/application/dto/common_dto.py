"""Common DTO definitions for pagination and generic search responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaginatedResponse[T](BaseModel):
    """Generic reusable paginated envelope for list endpoints.

    Attributes
    ----------
    items : list[T]
        List of item records on the current page.
    total : int
        Total number of records matching query criteria.
    page : int
        Current page number (1-based index).
    page_size : int
        Number of items per page.
    total_pages : int
        Total calculated page count.
    """

    model_config = ConfigDict(frozen=True)

    items: list[T] = Field(description="Page items")
    total: int = Field(description="Total record count")
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
