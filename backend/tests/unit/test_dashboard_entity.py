"""Comprehensive unit tests for the Dashboard domain entity."""

from __future__ import annotations

import pytest

from app.domain.entities.dashboard import Dashboard
from app.domain.exceptions import DomainValidationError


def test_dashboard_entity_creation_success() -> None:
    """Test valid Dashboard entity initialization and field assignments."""
    dashboard = Dashboard(
        id="dash-001",
        name="  Sales Performance  ",
        owner_id="  usr-100  ",
        dataset_id="  ds-200  ",
        description="Global sales metrics",
        layout_json={"columns": 3, "widgets": ["w1", "w2"]},
        is_public=True,
        is_active=True,
    )
    assert dashboard.id == "dash-001"
    assert dashboard.name == "Sales Performance"
    assert dashboard.owner_id == "usr-100"
    assert dashboard.dataset_id == "ds-200"
    assert dashboard.description == "Global sales metrics"
    assert dashboard.layout_json == {"columns": 3, "widgets": ["w1", "w2"]}
    assert dashboard.layout_config == {"columns": 3, "widgets": ["w1", "w2"]}
    assert dashboard.is_public is True
    assert dashboard.is_active is True
    assert dashboard.created_at is not None
    assert dashboard.updated_at is not None


def test_dashboard_entity_validation_failures() -> None:
    """Test domain invariant validation error raises for empty fields."""
    with pytest.raises(DomainValidationError, match="Dashboard name must not be empty"):
        Dashboard(id="d-1", name="   ", owner_id="u-1", dataset_id="ds-1")

    with pytest.raises(
        DomainValidationError, match="Dashboard owner_id must not be empty"
    ):
        Dashboard(id="d-1", name="Dashboard", owner_id="", dataset_id="ds-1")

    with pytest.raises(
        DomainValidationError, match="Dashboard dataset_id must not be empty"
    ):
        Dashboard(id="d-1", name="Dashboard", owner_id="u-1", dataset_id="  ")


def test_dashboard_entity_update_success() -> None:
    """Test updating Dashboard attributes updates updated_at and validates values."""
    dashboard = Dashboard(
        id="d-1", name="Original Name", owner_id="u-1", dataset_id="ds-1"
    )
    initial_updated_at = dashboard.updated_at

    dashboard.update(
        name="  Updated Title  ",
        description="New description",
        dataset_id="  ds-2  ",
        layout_json={"theme": "dark"},
        is_public=True,
        is_active=False,
    )

    assert dashboard.name == "Updated Title"
    assert dashboard.description == "New description"
    assert dashboard.dataset_id == "ds-2"
    assert dashboard.layout_json == {"theme": "dark"}
    assert dashboard.is_public is True
    assert dashboard.is_active is False
    assert dashboard.updated_at >= initial_updated_at


def test_dashboard_entity_update_validation_failures() -> None:
    """Test updating Dashboard with invalid attributes raises DomainValidationError."""
    dashboard = Dashboard(
        id="d-1", name="Original Name", owner_id="u-1", dataset_id="ds-1"
    )

    with pytest.raises(DomainValidationError, match="Dashboard name must not be empty"):
        dashboard.update(name="  ")

    with pytest.raises(
        DomainValidationError, match="Dashboard dataset_id must not be empty"
    ):
        dashboard.update(dataset_id="")
