"""Unit tests for BI Foundation mappers.

Covers DashboardMapper, ReportMapper, and DatasetMapper.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.entities.report import Report
from app.infrastructure.database.models import (
    DashboardModel,
    DatasetModel,
    ReportModel,
)
from app.infrastructure.mappers.dashboard_mapper import DashboardMapper
from app.infrastructure.mappers.dataset_mapper import DatasetMapper
from app.infrastructure.mappers.report_mapper import ReportMapper


def test_dashboard_mapper_roundtrip() -> None:
    """Test Dashboard domain entity to ORM model conversion and back."""
    now = datetime.now(UTC)
    entity = Dashboard(
        id="dash-1",
        name="Sales Dashboard",
        owner_id="u-1",
        dataset_id="ds-1",
        description="Overview",
        layout_json={"col": 2},
        is_public=True,
        created_at=now,
        updated_at=now,
    )

    model = DashboardMapper.to_model(entity)
    assert isinstance(model, DashboardModel)
    assert model.id == "dash-1"
    assert model.name == "Sales Dashboard"
    assert model.dataset_id == "ds-1"
    assert model.layout_config == {"col": 2}
    assert model.is_public is True

    domain_obj = DashboardMapper.to_domain(model)
    assert domain_obj.id == entity.id
    assert domain_obj.name == entity.name
    assert domain_obj.dataset_id == "ds-1"
    assert domain_obj.layout_config == entity.layout_config


def test_report_mapper_roundtrip() -> None:
    """Test Report domain entity to ORM model conversion and back."""
    now = datetime.now(UTC)
    entity = Report(
        id="rep-1",
        name="Report 1",
        query="SELECT 1",
        owner_id="u-1",
        description="Desc",
        dataset_id="ds-1",
        visualization_type="line",
        config={"y": "amount"},
        created_at=now,
        updated_at=now,
    )

    model = ReportMapper.to_model(entity)
    assert isinstance(model, ReportModel)
    assert model.id == "rep-1"
    assert model.dataset_id == "ds-1"

    domain_obj = ReportMapper.to_domain(model)
    assert domain_obj.id == entity.id
    assert domain_obj.visualization_type == "line"


def test_dataset_mapper_roundtrip() -> None:
    """Test Dataset domain entity to ORM model conversion and back."""
    now = datetime.now(UTC)
    entity = Dataset(
        id="ds-1",
        name="Dataset 1",
        source_type="snowflake",
        query_or_table="analytics.events",
        owner_id="u-1",
        description="Event store",
        schema_metadata={"columns": []},
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    model = DatasetMapper.to_model(entity)
    assert isinstance(model, DatasetModel)
    assert model.id == "ds-1"
    assert model.source_type == "snowflake"

    domain_obj = DatasetMapper.to_domain(model)
    assert domain_obj.id == entity.id
    assert domain_obj.query_or_table == "analytics.events"
