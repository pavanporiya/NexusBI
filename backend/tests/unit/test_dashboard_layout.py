"""Unit tests for Dashboard Layout value objects."""

import pytest

from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.dashboard_layout import (
    DashboardFilter,
    DashboardLayout,
    DashboardWidget,
    WidgetPosition,
)


def test_widget_position_validation() -> None:
    """Test position bounds and negative dimension rejection."""
    pos = WidgetPosition(x=0, y=0, w=6, h=4)
    assert pos.to_dict() == {"x": 0, "y": 0, "w": 6, "h": 4}

    with pytest.raises(DomainValidationError, match="non-negative integer"):
        WidgetPosition(x=-1, y=0, w=6, h=4)

    with pytest.raises(DomainValidationError, match="positive integer"):
        WidgetPosition(x=0, y=0, w=0, h=4)

    with pytest.raises(DomainValidationError, match="positive integer"):
        WidgetPosition(x=0, y=0, w=6, h=-2)


def test_dashboard_widget_validation() -> None:
    """Test dashboard widget construction and serialization."""
    pos = WidgetPosition(x=0, y=0, w=6, h=4)
    widget = DashboardWidget(
        id="w1",
        type="chart",
        title="Revenue Chart",
        position=pos,
        config={"chart_type": "bar"},
    )
    assert widget.id == "w1"
    assert widget.to_dict()["title"] == "Revenue Chart"

    with pytest.raises(DomainValidationError, match="Widget id must not be empty"):
        DashboardWidget(id="", type="chart", title="Title", position=pos)


def test_dashboard_filter_validation() -> None:
    """Test filter validation."""
    flt = DashboardFilter(id="f1", field="category", operator="eq", value="tech")
    assert flt.to_dict() == {
        "id": "f1",
        "field": "category",
        "operator": "eq",
        "value": "tech",
    }

    with pytest.raises(DomainValidationError, match="filter id must not be empty"):
        DashboardFilter(id="", field="category", operator="eq")


def test_dashboard_layout_validation_and_uniqueness() -> None:
    """Test duplicate widget ID rejection and layout columns validation."""
    pos = WidgetPosition(x=0, y=0, w=6, h=4)
    w1 = DashboardWidget(id="w1", type="chart", title="W1", position=pos)
    w2 = DashboardWidget(id="w1", type="chart", title="W2", position=pos)

    with pytest.raises(DomainValidationError, match="Duplicate widget ID"):
        DashboardLayout(widgets=(w1, w2))

    with pytest.raises(DomainValidationError, match="positive integer"):
        DashboardLayout(columns=0)


def test_dashboard_layout_dict_serialization() -> None:
    """Test layout JSON dict round-trip conversion."""
    data = {
        "columns": 12,
        "theme": "dark",
        "widgets": [
            {
                "id": "w1",
                "type": "chart",
                "title": "Chart 1",
                "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                "config": {"color": "blue"},
            }
        ],
        "filters": [
            {"id": "f1", "field": "date", "operator": "gte", "value": "2026-01-01"}
        ],
        "custom_setting": True,
    }

    layout = DashboardLayout.from_dict(data)
    assert layout.columns == 12
    assert layout.theme == "dark"
    assert len(layout.widgets) == 1
    assert layout.widgets[0].id == "w1"
    assert layout.extra_config == {"custom_setting": True}

    serialized = layout.to_dict()
    assert serialized["columns"] == 12
    assert serialized["theme"] == "dark"
    assert serialized["custom_setting"] is True
