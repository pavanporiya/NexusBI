"""Comprehensive unit tests for SQLAlchemyWidgetRepository."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.entities.widget import Widget
from app.domain.enums import WidgetType
from app.domain.value_objects.widget_configuration import WidgetConfiguration
from app.domain.value_objects.widget_position import WidgetPosition
from app.domain.value_objects.widget_size import WidgetSize
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import UserModel
from app.infrastructure.repositories.dashboard_repository import (
    SQLAlchemyDashboardRepository,
)
from app.infrastructure.repositories.dataset_repository import (
    SQLAlchemyDatasetRepository,
)
from app.infrastructure.repositories.widget_repository import (
    SQLAlchemyWidgetRepository,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    """In-memory SQLite session with owner user, dataset, and dashboard seeded."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    now = datetime.now(UTC)
    user = UserModel(
        id="usr-w-1",
        email="widget-owner@nexusbi.io",
        full_name="Widget Owner",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)

    ds_repo = SQLAlchemyDatasetRepository(session)
    ds = Dataset(
        id="ds-w-1",
        name="Widget Test Dataset",
        source_type="postgres",
        query_or_table="sales",
        owner_id="usr-w-1",
    )
    ds_repo.save(ds)

    dash_repo = SQLAlchemyDashboardRepository(session)
    dash = Dashboard(
        id="dash-w-1",
        name="Widget Test Dashboard",
        owner_id="usr-w-1",
        dataset_id="ds-w-1",
    )
    dash_repo.save(dash)

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


def test_widget_repository_crud(db_session: Session) -> None:
    """Test saving, fetching, updating, listing, and deleting widgets."""
    repo = SQLAlchemyWidgetRepository(db_session)

    widget1 = Widget(
        id="widget-1",
        dashboard_id="dash-w-1",
        dataset_id="ds-w-1",
        title="Revenue Chart",
        widget_type=WidgetType.BAR_CHART,
        position=WidgetPosition(row=0, column=0),
        size=WidgetSize(width=6, height=4),
        configuration=WidgetConfiguration(metrics=("revenue",)),
        refresh_interval=30,
        is_visible=True,
    )

    widget2 = Widget(
        id="widget-2",
        dashboard_id="dash-w-1",
        dataset_id="ds-w-1",
        title="Total Customers KPI",
        widget_type=WidgetType.KPI,
        position=WidgetPosition(row=1, column=0),
        size=WidgetSize(width=3, height=2),
    )

    # Save
    repo.save(widget1)
    repo.save(widget2)

    # Get by ID
    fetched = repo.get_by_id("widget-1")
    assert fetched is not None
    assert fetched.title == "Revenue Chart"
    assert fetched.widget_type == WidgetType.BAR_CHART
    assert fetched.position.row == 0
    assert fetched.size.width == 6
    assert fetched.refresh_interval == 30

    # Get by dashboard and title
    by_title = repo.get_by_dashboard_and_title("dash-w-1", "Revenue Chart")
    assert by_title is not None
    assert by_title.id == "widget-1"

    # List by dashboard ID
    widgets = repo.list_by_dashboard_id("dash-w-1")
    assert len(widgets) == 2
    assert widgets[0].id == "widget-1"
    assert widgets[1].id == "widget-2"

    # Update
    widget1.update(title="Updated Revenue Chart", refresh_interval=60)
    repo.save(widget1)

    updated_fetch = repo.get_by_id("widget-1")
    assert updated_fetch is not None
    assert updated_fetch.title == "Updated Revenue Chart"
    assert updated_fetch.refresh_interval == 60

    # Delete
    assert repo.delete("widget-1") is True
    assert repo.get_by_id("widget-1") is None
    assert repo.delete("non-existent-widget") is False
