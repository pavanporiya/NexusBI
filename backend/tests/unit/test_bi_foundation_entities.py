"""Unit tests for BI Foundation domain entities: Dashboard, Report, Dataset."""

from __future__ import annotations

import pytest

from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.entities.report import Report
from app.domain.exceptions import DomainValidationError


def test_dashboard_entity_creation_and_validation() -> None:
    """Test Dashboard entity initialization and invariants."""
    dashboard = Dashboard(
        id="dash-123",
        name="  Executive Overview  ",
        owner_id="user-456",
        dataset_id="ds-789",
        description="High level metrics",
        layout_json={"widgets": [1, 2]},
        is_public=True,
    )
    assert dashboard.id == "dash-123"
    assert dashboard.name == "Executive Overview"
    assert dashboard.owner_id == "user-456"
    assert dashboard.dataset_id == "ds-789"
    assert dashboard.description == "High level metrics"
    assert dashboard.layout_config == {"widgets": [1, 2]}
    assert dashboard.is_public is True


def test_dashboard_entity_validation_failures() -> None:
    """Test Dashboard validation error on empty name or owner or dataset_id."""
    msg = "Dashboard name must not be empty"
    with pytest.raises(DomainValidationError, match=msg):
        Dashboard(id="d-1", name="   ", owner_id="u-1", dataset_id="ds-1")

    msg_owner = "Dashboard owner_id must not be empty"
    with pytest.raises(DomainValidationError, match=msg_owner):
        Dashboard(id="d-1", name="Valid Name", owner_id="", dataset_id="ds-1")

    msg_dataset = "Dashboard dataset_id must not be empty"
    with pytest.raises(DomainValidationError, match=msg_dataset):
        Dashboard(id="d-1", name="Valid Name", owner_id="u-1", dataset_id="")


def test_dashboard_entity_update() -> None:
    """Test Dashboard update method."""
    dashboard = Dashboard(
        id="d-1", name="Original Name", owner_id="u-1", dataset_id="ds-1"
    )
    old_updated_at = dashboard.updated_at

    dashboard.update(name=" New Name ", description="Updated desc", is_public=True)
    assert dashboard.name == "New Name"
    assert dashboard.description == "Updated desc"
    assert dashboard.is_public is True
    assert dashboard.updated_at >= old_updated_at

    msg = "Dashboard name must not be empty"
    with pytest.raises(DomainValidationError, match=msg):
        dashboard.update(name="  ")


def test_report_entity_creation_and_update() -> None:
    """Test Report entity creation, validation, and update."""
    report = Report(
        id="rep-1",
        name=" Monthly Sales ",
        dataset_id="ds-1",
        owner_id="user-1",
        query="SELECT * FROM sales",
        visualization_type="bar",
        config={"color": "blue"},
    )
    assert report.name == "Monthly Sales"
    assert report.dataset_id == "ds-1"
    assert report.query == "SELECT * FROM sales"

    report.update(name="Annual Sales", query="SELECT * FROM annual_sales")
    assert report.name == "Annual Sales"
    assert report.query == "SELECT * FROM annual_sales"

    msg = "Report dataset_id must not be empty"
    with pytest.raises(DomainValidationError, match=msg):
        Report(id="r-2", name="Valid", dataset_id="", owner_id="u-1")


def test_dataset_entity_creation_and_update() -> None:
    """Test Dataset entity creation, validation, and update."""
    dataset = Dataset(
        id="ds-1",
        name=" Sales Transactions ",
        source_type="postgres",
        query_or_table="public.transactions",
        owner_id="user-1",
        schema_metadata={"columns": ["id", "amount"]},
    )
    assert dataset.name == "Sales Transactions"
    assert dataset.source_type == "postgres"
    assert dataset.query_or_table == "public.transactions"

    dataset.update(name="All Transactions", is_active=False)
    assert dataset.name == "All Transactions"
    assert dataset.is_active is False

    msg = "Dataset source_type must not be empty"
    with pytest.raises(DomainValidationError, match=msg):
        Dataset(
            id="ds-2",
            name="Valid",
            source_type="",
            query_or_table="tbl",
            owner_id="u-1",
        )
