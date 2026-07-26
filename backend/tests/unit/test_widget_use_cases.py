"""Unit tests for Widget application use cases."""

from __future__ import annotations

from typing import Any

import pytest

from app.application.dto.widget_dto import (
    CreateWidgetDTO,
    MoveWidgetDTO,
    ResizeWidgetDTO,
    ToggleVisibilityDTO,
    UpdateWidgetDTO,
    WidgetPositionDTO,
    WidgetSizeDTO,
)
from app.application.use_cases.create_widget import CreateWidgetUseCase
from app.application.use_cases.delete_widget import DeleteWidgetUseCase
from app.application.use_cases.get_widget import GetWidgetUseCase
from app.application.use_cases.list_widgets import ListWidgetsUseCase
from app.application.use_cases.move_widget import MoveWidgetUseCase
from app.application.use_cases.resize_widget import ResizeWidgetUseCase
from app.application.use_cases.toggle_visibility import ToggleVisibilityUseCase
from app.application.use_cases.update_widget import UpdateWidgetUseCase
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.dashboard import Dashboard
from app.domain.entities.dataset import Dataset
from app.domain.entities.widget import Widget
from app.domain.enums import WidgetType


class InMemoryWidgetRepo:
    """In-memory stub implementation for IWidgetRepository."""

    def __init__(self) -> None:
        self.storage: dict[str, Widget] = {}

    def get_by_id(self, widget_id: str) -> Widget | None:
        return self.storage.get(widget_id)

    def list_by_dashboard_id(self, dashboard_id: str) -> list[Widget]:
        return [w for w in self.storage.values() if w.dashboard_id == dashboard_id]

    def get_by_dashboard_and_title(
        self, dashboard_id: str, title: str
    ) -> Widget | None:
        for w in self.storage.values():
            if w.dashboard_id == dashboard_id and w.title == title:
                return w
        return None

    def save(self, widget: Widget) -> Widget:
        self.storage[widget.id] = widget
        return widget

    def delete(self, widget_id: str) -> bool:
        return self.storage.pop(widget_id, None) is not None


class InMemoryDashboardRepo:
    """In-memory stub implementation for IDashboardRepository."""

    def __init__(self) -> None:
        self.storage: dict[str, Dashboard] = {}

    def get_by_id(self, dashboard_id: str) -> Dashboard | None:
        return self.storage.get(dashboard_id)

    def save(self, dashboard: Dashboard) -> Dashboard:
        self.storage[dashboard.id] = dashboard
        return dashboard

    def delete(self, dashboard_id: str) -> bool:
        return self.storage.pop(dashboard_id, None) is not None

    def list(self, _params: Any) -> tuple[list[Dashboard], int]:

        items = list(self.storage.values())
        return items, len(items)


class InMemoryDatasetRepo:
    """In-memory stub implementation for IDatasetRepository."""

    def __init__(self) -> None:
        self.storage: dict[str, Dataset] = {}

    def get_by_id(self, dataset_id: str) -> Dataset | None:
        return self.storage.get(dataset_id)

    def save(self, dataset: Dataset) -> Dataset:
        self.storage[dataset.id] = dataset
        return dataset

    def delete(self, dataset_id: str) -> bool:
        return self.storage.pop(dataset_id, None) is not None

    def list(self, _params: Any) -> tuple[list[Dataset], int]:

        items = list(self.storage.values())
        return items, len(items)


def test_create_widget_use_case_success() -> None:
    """Test CreateWidgetUseCase happy path."""
    widget_repo = InMemoryWidgetRepo()
    dashboard_repo = InMemoryDashboardRepo()
    dataset_repo = InMemoryDatasetRepo()

    dashboard_repo.storage["dash-1"] = Dashboard(
        id="dash-1", name="Sales Dash", owner_id="u-1", dataset_id="ds-1"
    )
    dataset_repo.storage["ds-1"] = Dataset(
        id="ds-1",
        name="Sales Data",
        source_type="pg",
        query_or_table="t1",
        owner_id="u-1",
    )

    use_case = CreateWidgetUseCase(widget_repo, dashboard_repo, dataset_repo)

    dto = CreateWidgetDTO(
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="Monthly Revenue",
        widget_type="BAR_CHART",
        position=WidgetPositionDTO(row=0, column=0),
        size=WidgetSizeDTO(width=6, height=4),
        configuration={"sort_order": "asc"},
        refresh_interval=60,
    )

    res = use_case.execute(dto)
    assert res.title == "Monthly Revenue"
    assert res.widget_type == "bar_chart"
    assert res.dashboard_id == "dash-1"
    assert res.position.row == 0
    assert res.size.width == 6


def test_create_widget_missing_dashboard_or_dataset() -> None:
    """Test CreateWidgetUseCase raises EntityNotFoundError when missing."""

    widget_repo = InMemoryWidgetRepo()
    dashboard_repo = InMemoryDashboardRepo()
    dataset_repo = InMemoryDatasetRepo()

    use_case = CreateWidgetUseCase(widget_repo, dashboard_repo, dataset_repo)

    dto = CreateWidgetDTO(
        dashboard_id="non-existent-dash",
        dataset_id="ds-1",
        title="Widget",
        widget_type="KPI",
    )

    with pytest.raises(EntityNotFoundError, match="Dashboard"):
        use_case.execute(dto)

    dashboard_repo.storage["dash-1"] = Dashboard(
        id="dash-1", name="Sales Dash", owner_id="u-1", dataset_id="ds-1"
    )

    with pytest.raises(EntityNotFoundError, match="Dataset"):
        use_case.execute(dto, dashboard_id="dash-1")


def test_create_widget_duplicate_title() -> None:
    """Test CreateWidgetUseCase raises DuplicateEntityError on duplicate title."""
    widget_repo = InMemoryWidgetRepo()
    dashboard_repo = InMemoryDashboardRepo()
    dataset_repo = InMemoryDatasetRepo()

    dashboard_repo.storage["dash-1"] = Dashboard(
        id="dash-1", name="Dash", owner_id="u-1", dataset_id="ds-1"
    )
    dataset_repo.storage["ds-1"] = Dataset(
        id="ds-1", name="DS", source_type="pg", query_or_table="t1", owner_id="u-1"
    )

    existing = Widget(
        id="w-1",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="Duplicate Title",
        widget_type=WidgetType.KPI,
    )
    widget_repo.save(existing)

    use_case = CreateWidgetUseCase(widget_repo, dashboard_repo, dataset_repo)
    dto = CreateWidgetDTO(
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="Duplicate Title",
        widget_type="KPI",
    )

    with pytest.raises(DuplicateEntityError, match="Widget"):
        use_case.execute(dto)


def test_get_widget_use_case() -> None:
    """Test GetWidgetUseCase retrieving widget by ID."""
    widget_repo = InMemoryWidgetRepo()
    widget = Widget(
        id="w-100",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="KPI Widget",
        widget_type=WidgetType.KPI,
    )
    widget_repo.save(widget)

    use_case = GetWidgetUseCase(widget_repo)
    res = use_case.execute("w-100")
    assert res.id == "w-100"
    assert res.title == "KPI Widget"

    with pytest.raises(EntityNotFoundError):
        use_case.execute("missing-id")


def test_update_widget_use_case() -> None:
    """Test UpdateWidgetUseCase updating title, type, configuration."""
    widget_repo = InMemoryWidgetRepo()
    dataset_repo = InMemoryDatasetRepo()

    dataset_repo.storage["ds-1"] = Dataset(
        id="ds-1", name="DS1", source_type="pg", query_or_table="t1", owner_id="u-1"
    )
    dataset_repo.storage["ds-2"] = Dataset(
        id="ds-2", name="DS2", source_type="pg", query_or_table="t2", owner_id="u-1"
    )

    widget = Widget(
        id="w-1",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="Initial Title",
        widget_type=WidgetType.BAR_CHART,
    )
    widget_repo.save(widget)

    use_case = UpdateWidgetUseCase(widget_repo, dataset_repo)
    dto = UpdateWidgetDTO(
        title="New Title",
        dataset_id="ds-2",
        widget_type="LINE_CHART",
    )

    res = use_case.execute("w-1", dto)
    assert res.title == "New Title"
    assert res.dataset_id == "ds-2"
    assert res.widget_type == "line_chart"


def test_move_resize_toggle_visibility_use_cases() -> None:
    """Test MoveWidgetUseCase, ResizeWidgetUseCase, ToggleVisibilityUseCase."""
    widget_repo = InMemoryWidgetRepo()
    widget = Widget(
        id="w-1",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="Title",
        widget_type=WidgetType.BAR_CHART,
    )
    widget_repo.save(widget)

    # Move
    move_uc = MoveWidgetUseCase(widget_repo)
    res_move = move_uc.execute("w-1", MoveWidgetDTO(row=4, column=2))
    assert res_move.position.row == 4
    assert res_move.position.column == 2

    # Resize
    resize_uc = ResizeWidgetUseCase(widget_repo)
    res_resize = resize_uc.execute("w-1", ResizeWidgetDTO(width=8, height=6))
    assert res_resize.size.width == 8
    assert res_resize.size.height == 6

    # Toggle visibility
    toggle_uc = ToggleVisibilityUseCase(widget_repo)
    res_toggle1 = toggle_uc.execute("w-1", ToggleVisibilityDTO(is_visible=False))
    assert res_toggle1.is_visible is False

    res_toggle2 = toggle_uc.execute("w-1")
    assert res_toggle2.is_visible is True


def test_delete_and_list_widgets_use_cases() -> None:
    """Test DeleteWidgetUseCase and ListWidgetsUseCase."""
    widget_repo = InMemoryWidgetRepo()
    dashboard_repo = InMemoryDashboardRepo()

    dashboard_repo.storage["dash-1"] = Dashboard(
        id="dash-1", name="Dash", owner_id="u-1", dataset_id="ds-1"
    )

    w1 = Widget(
        id="w-1",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="W1",
        widget_type=WidgetType.KPI,
    )
    w2 = Widget(
        id="w-2",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="W2",
        widget_type=WidgetType.TABLE,
    )
    widget_repo.save(w1)
    widget_repo.save(w2)

    list_uc = ListWidgetsUseCase(widget_repo, dashboard_repo)
    items = list_uc.execute("dash-1")
    assert len(items) == 2

    delete_uc = DeleteWidgetUseCase(widget_repo)
    assert delete_uc.execute("w-1") is True

    items_after = list_uc.execute("dash-1")
    assert len(items_after) == 1
    assert items_after[0].id == "w-2"
