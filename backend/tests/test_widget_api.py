"""Comprehensive REST API tests for Dashboard Widget Engine endpoints.

Tests widget creation, retrieval, listing, updating, deletion, moving,
resizing, and visibility toggling.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_create_widget_use_case,
    get_current_user,
    get_delete_widget_use_case,
    get_get_widget_use_case,
    get_list_widgets_use_case,
    get_move_widget_use_case,
    get_resize_widget_use_case,
    get_toggle_visibility_use_case,
    get_update_widget_use_case,
)
from app.application.dto.widget_dto import WidgetDTO, WidgetPositionDTO, WidgetSizeDTO
from app.application.services.interfaces import IAuthorizationService
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User


@pytest.fixture
def sample_user() -> User:
    """Authenticated user with dashboard permissions."""
    perm_read = Permission(
        id="p-db-r", resource="dashboard", action="read", description=""
    )
    perm_update = Permission(
        id="p-db-u", resource="dashboard", action="update", description=""
    )
    perm_delete = Permission(
        id="p-db-d", resource="dashboard", action="delete", description=""
    )
    role = Role(
        id="r-widget-1",
        name="WidgetAdmin",
        permissions=[perm_read, perm_update, perm_delete],
    )
    return User(id="usr-w-001", email="widget-user@nexusbi.io", roles=[role])


@pytest.fixture
def sample_widget_dto() -> WidgetDTO:
    """Sample WidgetDTO object for mock responses."""
    now = datetime.now(UTC)
    return WidgetDTO(
        id="w-100",
        dashboard_id="dash-1",
        dataset_id="ds-1",
        title="Revenue Chart",
        widget_type="bar_chart",
        position=WidgetPositionDTO(row=0, column=0),
        size=WidgetSizeDTO(width=6, height=4),
        configuration={"sort_order": "asc"},
        refresh_interval=60,
        is_visible=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_auth_service() -> MagicMock:
    """Mock IAuthorizationService that grants permissions."""
    mock = MagicMock(spec=IAuthorizationService)
    mock.has_permission.return_value = True
    return mock


@pytest.fixture
def test_app(
    sample_user: User,
    mock_auth_service: MagicMock,
) -> FastAPI:
    """Create test FastAPI application instance with mocked auth."""
    from app.main import create_app

    app = create_app()

    app.dependency_overrides[get_current_user] = lambda: sample_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service

    return app


def test_create_widget_api_success(
    test_app: FastAPI, sample_widget_dto: WidgetDTO
) -> None:
    """Test POST /api/v1/dashboards/{dashboard_id}/widgets success."""
    mock_create_uc = MagicMock()
    mock_create_uc.execute.return_value = sample_widget_dto
    test_app.dependency_overrides[get_create_widget_use_case] = lambda: mock_create_uc

    client = TestClient(test_app)
    response = client.post(
        "/api/v1/dashboards/dash-1/widgets",
        json={
            "dataset_id": "ds-1",
            "title": "Revenue Chart",
            "widget_type": "BAR_CHART",
            "position": {"row": 0, "column": 0},
            "size": {"width": 6, "height": 4},
            "configuration": {"sort_order": "asc"},
            "refresh_interval": 60,
        },
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 210 or response.status_code == 201
    data = response.json()
    assert data["id"] == "w-100"
    assert data["title"] == "Revenue Chart"
    assert data["widget_type"] == "bar_chart"


def test_create_widget_api_duplicate_title(test_app: FastAPI) -> None:
    """Test POST widgets duplicate title conflict error."""

    mock_create_uc = MagicMock()
    mock_create_uc.execute.side_effect = DuplicateEntityError(
        "Widget", "Dashboard 'dash-1' with title 'Revenue Chart'"
    )
    test_app.dependency_overrides[get_create_widget_use_case] = lambda: mock_create_uc

    client = TestClient(test_app)
    response = client.post(
        "/api/v1/dashboards/dash-1/widgets",
        json={
            "dataset_id": "ds-1",
            "title": "Revenue Chart",
            "widget_type": "BAR_CHART",
        },
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "NBI-4002"


def test_list_widgets_api(test_app: FastAPI, sample_widget_dto: WidgetDTO) -> None:
    """Test GET /api/v1/dashboards/{dashboard_id}/widgets."""
    mock_list_uc = MagicMock()
    mock_list_uc.execute.return_value = [sample_widget_dto]
    test_app.dependency_overrides[get_list_widgets_use_case] = lambda: mock_list_uc

    client = TestClient(test_app)
    response = client.get(
        "/api/v1/dashboards/dash-1/widgets",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "w-100"


def test_get_widget_by_id_api(test_app: FastAPI, sample_widget_dto: WidgetDTO) -> None:
    """Test GET /api/v1/widgets/{widget_id} success and 404."""
    mock_get_uc = MagicMock()
    mock_get_uc.execute.return_value = sample_widget_dto
    test_app.dependency_overrides[get_get_widget_use_case] = lambda: mock_get_uc

    client = TestClient(test_app)
    response = client.get(
        "/api/v1/widgets/w-100",
        headers={"Authorization": "Bearer fake_token"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == "w-100"

    # Test 404
    mock_get_uc.execute.side_effect = EntityNotFoundError("Widget", "missing-w")
    response_404 = client.get(
        "/api/v1/widgets/missing-w",
        headers={"Authorization": "Bearer fake_token"},
    )
    assert response_404.status_code == 404


def test_update_widget_api(test_app: FastAPI, sample_widget_dto: WidgetDTO) -> None:
    """Test PUT/PATCH /api/v1/widgets/{widget_id}."""
    mock_update_uc = MagicMock()
    mock_update_uc.execute.return_value = sample_widget_dto
    test_app.dependency_overrides[get_update_widget_use_case] = lambda: mock_update_uc

    client = TestClient(test_app)
    response = client.patch(
        "/api/v1/widgets/w-100",
        json={"title": "Updated Title"},
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == "w-100"


def test_move_widget_api(test_app: FastAPI, sample_widget_dto: WidgetDTO) -> None:
    """Test PATCH /api/v1/widgets/{widget_id}/move."""
    mock_move_uc = MagicMock()
    mock_move_uc.execute.return_value = sample_widget_dto
    test_app.dependency_overrides[get_move_widget_use_case] = lambda: mock_move_uc

    client = TestClient(test_app)
    response = client.patch(
        "/api/v1/widgets/w-100/move",
        json={"row": 2, "column": 4},
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200


def test_resize_widget_api(test_app: FastAPI, sample_widget_dto: WidgetDTO) -> None:
    """Test PATCH /api/v1/widgets/{widget_id}/resize."""
    mock_resize_uc = MagicMock()
    mock_resize_uc.execute.return_value = sample_widget_dto
    test_app.dependency_overrides[get_resize_widget_use_case] = lambda: mock_resize_uc

    client = TestClient(test_app)
    response = client.patch(
        "/api/v1/widgets/w-100/resize",
        json={"width": 8, "height": 6},
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200


def test_toggle_visibility_api(test_app: FastAPI, sample_widget_dto: WidgetDTO) -> None:
    """Test PATCH /api/v1/widgets/{widget_id}/visibility."""
    mock_toggle_uc = MagicMock()
    mock_toggle_uc.execute.return_value = sample_widget_dto
    test_app.dependency_overrides[get_toggle_visibility_use_case] = lambda: (
        mock_toggle_uc
    )

    client = TestClient(test_app)
    response = client.patch(
        "/api/v1/widgets/w-100/visibility",
        json={"is_visible": False},
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200


def test_delete_widget_api(test_app: FastAPI) -> None:
    """Test DELETE /api/v1/widgets/{widget_id}."""
    mock_delete_uc = MagicMock()
    mock_delete_uc.execute.return_value = True
    test_app.dependency_overrides[get_delete_widget_use_case] = lambda: mock_delete_uc

    client = TestClient(test_app)
    response = client.delete(
        "/api/v1/widgets/w-100",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 204
