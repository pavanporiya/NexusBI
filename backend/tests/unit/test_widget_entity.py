"""Unit tests for Widget domain aggregate and value objects."""

from __future__ import annotations

import pytest

from app.domain.entities.widget import Widget
from app.domain.enums import WidgetType
from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.widget_configuration import WidgetConfiguration
from app.domain.value_objects.widget_position import WidgetPosition
from app.domain.value_objects.widget_size import WidgetSize


def test_widget_position_valid() -> None:
    """Test creating a valid WidgetPosition."""
    pos = WidgetPosition(row=2, column=4)
    assert pos.row == 2
    assert pos.column == 4
    assert pos.to_dict() == {"row": 2, "column": 4}
    assert WidgetPosition.from_dict({"row": 2, "column": 4}) == pos


def test_widget_position_invalid() -> None:
    """Test rejecting negative positions."""
    with pytest.raises(DomainValidationError, match="non-negative integer"):
        WidgetPosition(row=-1, column=0)

    with pytest.raises(DomainValidationError, match="non-negative integer"):
        WidgetPosition(row=0, column=-2)


def test_widget_size_valid() -> None:
    """Test creating a valid WidgetSize."""
    size = WidgetSize(width=6, height=4)
    assert size.width == 6
    assert size.height == 4
    assert size.to_dict() == {"width": 6, "height": 4}
    assert WidgetSize.from_dict({"width": 6, "height": 4}) == size


def test_widget_size_invalid() -> None:
    """Test rejecting negative or zero dimensions."""
    with pytest.raises(DomainValidationError, match="positive integer"):
        WidgetSize(width=0, height=4)

    with pytest.raises(DomainValidationError, match="positive integer"):
        WidgetSize(width=6, height=-1)


def test_widget_configuration() -> None:
    """Test WidgetConfiguration serialization and validation."""
    config = WidgetConfiguration(
        metrics=("revenue", "sales"),
        dimensions=("region",),
        filters={"region": "US"},
        sort_by="revenue",
        sort_order="desc",
        limit=10,
        options={"color": "blue"},
    )
    assert config.metrics == ("revenue", "sales")
    assert config.sort_order == "desc"
    data = config.to_dict()
    assert data["metrics"] == ["revenue", "sales"]
    assert data["limit"] == 10

    reconstructed = WidgetConfiguration.from_dict(data)
    assert reconstructed.metrics == ("revenue", "sales")
    assert reconstructed.limit == 10


def test_widget_entity_creation() -> None:
    """Test creating a valid Widget aggregate entity."""
    widget = Widget(
        id="widget-123",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="Revenue Trends",
        widget_type=WidgetType.LINE_CHART,
        position=WidgetPosition(row=0, column=0),
        size=WidgetSize(width=6, height=4),
        configuration=WidgetConfiguration(metrics=("revenue",)),
        refresh_interval=60,
        is_visible=True,
    )
    assert widget.id == "widget-123"
    assert widget.dashboard_id == "dash-1"
    assert widget.dataset_id == "ds-1"
    assert widget.title == "Revenue Trends"
    assert widget.widget_type == WidgetType.LINE_CHART
    assert widget.position.row == 0
    assert widget.size.width == 6
    assert widget.refresh_interval == 60
    assert widget.is_visible is True


@pytest.mark.parametrize(
    ("widget_type_input", "expected_enum"),
    [
        ("kpi", WidgetType.KPI),
        ("KPI", WidgetType.KPI),
        ("BAR_CHART", WidgetType.BAR_CHART),
        ("table", WidgetType.TABLE),
        ("text", WidgetType.TEXT),
        ("donut_chart", WidgetType.DONUT_CHART),
    ],
)
def test_widget_type_enum_parsing(
    widget_type_input: str, expected_enum: WidgetType
) -> None:
    """Test parsing widget type strings into WidgetType enums."""
    widget = Widget(
        id="w-1",
        dashboard_id="d-1",
        dataset_id="ds-1",
        title="Test Widget",
        widget_type=widget_type_input,
    )
    assert widget.widget_type == expected_enum


def test_widget_validation_rejects_missing_dataset() -> None:
    """Test rejecting empty dataset_id."""
    with pytest.raises(DomainValidationError, match="dataset_id must not be empty"):
        Widget(
            id="w-1",
            dashboard_id="d-1",
            dataset_id="",
            title="Widget",
            widget_type=WidgetType.KPI,
        )


def test_widget_validation_rejects_empty_fields() -> None:
    """Test rejecting empty id, dashboard_id, title, or invalid widget type."""
    with pytest.raises(DomainValidationError, match="id must not be empty"):
        Widget(
            id="",
            dashboard_id="d-1",
            dataset_id="ds-1",
            title="Widget",
            widget_type=WidgetType.KPI,
        )

    with pytest.raises(DomainValidationError, match="dashboard_id must not be empty"):
        Widget(
            id="w-1",
            dashboard_id="",
            dataset_id="ds-1",
            title="Widget",
            widget_type=WidgetType.KPI,
        )

    with pytest.raises(DomainValidationError, match="title must not be empty"):
        Widget(
            id="w-1",
            dashboard_id="d-1",
            dataset_id="ds-1",
            title="",
            widget_type=WidgetType.KPI,
        )

    with pytest.raises(DomainValidationError, match="Invalid widget_type"):
        Widget(
            id="w-1",
            dashboard_id="d-1",
            dataset_id="ds-1",
            title="Widget",
            widget_type="INVALID_TYPE",
        )


def test_widget_domain_methods() -> None:
    """Test move, resize, toggle_visibility, and update domain methods."""
    widget = Widget(
        id="w-1",
        dashboard_id="d-1",
        dataset_id="ds-1",
        title="Original Title",
        widget_type=WidgetType.BAR_CHART,
        position=WidgetPosition(row=0, column=0),
        size=WidgetSize(width=2, height=2),
    )

    widget.move(row=3, column=5)
    assert widget.position == WidgetPosition(row=3, column=5)

    widget.resize(width=8, height=4)
    assert widget.size == WidgetSize(width=8, height=4)

    widget.toggle_visibility(False)
    assert widget.is_visible is False

    widget.toggle_visibility()
    assert widget.is_visible is True

    widget.update(title="Updated Title", widget_type="PIE_CHART", refresh_interval=120)
    assert widget.title == "Updated Title"
    assert widget.widget_type == WidgetType.PIE_CHART
    assert widget.refresh_interval == 120
