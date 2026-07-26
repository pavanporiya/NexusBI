"""API tests for Universal Chart Engine endpoints."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_authorization_service, get_current_user
from app.application.services.interfaces import IAuthorizationService
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.main import app


def make_chart_request(
    *,
    rows: list[dict[str, object]] | None = None,
    columns: list[dict[str, str]] | None = None,
    config_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a reusable API payload."""
    if rows is None:
        rows = [
            {"month": "Jan", "sales": 10, "profit": 2},
            {"month": "Feb", "sales": 15, "profit": 4},
            {"month": "Mar", "sales": 20, "profit": 6},
        ]
    columns = columns or [
        {"name": "month", "type": "string"},
        {"name": "sales", "type": "integer"},
        {"name": "profit", "type": "integer"},
    ]
    config: dict[str, object] = {
        "chart_type": "bar_chart",
        "x_axis_column": "month",
        "y_axis_columns": ["sales"],
        "aggregation": "sum",
        "title": "Monthly Sales",
        "metadata": {"requested_by": "tests"},
    }
    if config_overrides:
        config.update(config_overrides)

    return {
        "result": {
            "rows": rows,
            "columns": columns,
            "column_types": {column["name"]: column["type"] for column in columns},
            "execution_time": 0.01,
            "row_count": len(rows),
            "metadata": {
                "statistics": {
                    "query_plan": "SELECT ...",
                    "rows_scanned": len(rows),
                    "bytes_processed": 128,
                    "cache_hit": False,
                },
                "execution_time": 0.01,
                "row_count": len(rows),
                "columns": columns,
                "truncated": False,
                "limit": None,
                "offset": None,
            },
        },
        "config": config,
    }


@pytest.fixture
def sample_user() -> User:
    permission = Permission(
        id="perm-datasets-read",
        resource="datasets",
        action="read",
        description="",
    )
    role = Role(id="role-1", name="Analyst", permissions=[permission])
    return User(id="user-1", email="charts@nexusbi.io", roles=[role])


@pytest.fixture
def mock_auth_service() -> MagicMock:
    auth_svc = MagicMock(spec=IAuthorizationService)
    auth_svc.has_permission.return_value = True
    auth_svc.has_any_permission.return_value = True
    auth_svc.has_all_permissions.return_value = True
    auth_svc.can_access.return_value = True
    auth_svc.get_user_permissions.return_value = {"datasets:read"}
    auth_svc.get_user_roles.return_value = {"Analyst"}
    return auth_svc


@pytest.fixture
def client(
    sample_user: User,
    mock_auth_service: MagicMock,
) -> Generator[TestClient]:
    app.dependency_overrides[get_current_user] = lambda: sample_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_generate_chart_returns_formatted_result(client: TestClient) -> None:
    response = client.post("/api/v1/charts/generate", json=make_chart_request())

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Monthly Sales"
    assert data["labels"] == ["Jan", "Feb", "Mar"]
    assert data["series"][0]["name"] == "sales"
    assert data["metadata"]["chart_type"] == "bar_chart"
    assert data["statistics"]["sum"] == 45


def test_preview_chart_uses_same_chart_pipeline(client: TestClient) -> None:
    payload = make_chart_request(
        config_overrides={"chart_type": "line_chart", "title": "Preview"}
    )

    response = client.post("/api/v1/charts/preview", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Preview"
    assert data["series"][0]["chart_type"] == "line_chart"


def test_validate_chart_returns_valid_payload(client: TestClient) -> None:
    response = client.post("/api/v1/charts/validate", json=make_chart_request())

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "valid": True,
        "message": (
            "Chart configuration is valid and compatible with the dataset schema."
        ),
        "errors": [],
    }


def test_validate_chart_rejects_empty_dataset(client: TestClient) -> None:
    payload = make_chart_request(rows=[])

    response = client.post("/api/v1/charts/validate", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert "Dataset is empty" in data["message"]


def test_generate_chart_rejects_invalid_chart_type(client: TestClient) -> None:
    payload = make_chart_request(config_overrides={"chart_type": "unknown"})

    response = client.post("/api/v1/charts/generate", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "NBI-1001"


def test_generate_chart_rejects_missing_x_axis(client: TestClient) -> None:
    payload = make_chart_request(config_overrides={"x_axis_column": None})

    response = client.post("/api/v1/charts/generate", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "X-axis column is required" in response.json()["error"]["detail"]


def test_generate_chart_supports_large_dataset(client: TestClient) -> None:
    rows = [{"month": f"M{i}", "sales": i, "profit": i // 2} for i in range(1, 251)]
    payload = make_chart_request(rows=rows)

    response = client.post("/api/v1/charts/generate", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["labels"]) == 250
    assert data["statistics"]["count"] == 250


def test_generate_chart_supports_single_row_dataset(client: TestClient) -> None:
    payload = make_chart_request(rows=[{"month": "Jan", "sales": 10, "profit": 2}])

    response = client.post("/api/v1/charts/generate", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["labels"] == ["Jan"]
    assert data["series"][0]["data"][0]["y"] == 10


def test_generate_chart_supports_single_column_dataset_for_table(
    client: TestClient,
) -> None:
    payload = make_chart_request(
        rows=[{"month": "Jan"}, {"month": "Feb"}],
        columns=[{"name": "month", "type": "string"}],
        config_overrides={
            "chart_type": "table",
            "x_axis_column": None,
            "y_axis_columns": [],
            "title": "Months",
        },
    )

    response = client.post("/api/v1/charts/generate", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["labels"] == ["month"]
    assert data["series"][0]["data"][0]["value"] == "Jan"


def test_generate_chart_supports_multiple_series(client: TestClient) -> None:
    payload = make_chart_request(
        config_overrides={"y_axis_columns": ["sales", "profit"]}
    )

    response = client.post("/api/v1/charts/generate", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert [series["name"] for series in data["series"]] == ["sales", "profit"]


def test_preview_chart_rejects_null_metric_column(client: TestClient) -> None:
    payload = make_chart_request(
        rows=[
            {"month": "Jan", "sales": None, "profit": 2},
            {"month": "Feb", "sales": None, "profit": 4},
        ]
    )

    response = client.post("/api/v1/charts/preview", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "contains only null values" in response.json()["error"]["detail"]


def test_validate_chart_rejects_duplicate_series(client: TestClient) -> None:
    payload = make_chart_request(
        config_overrides={"y_axis_columns": ["sales", "sales"]}
    )

    response = client.post("/api/v1/charts/validate", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert "Duplicate series columns" in data["message"]


def test_generate_chart_missing_required_request_field_returns_422(
    client: TestClient,
) -> None:
    payload = make_chart_request()
    config = payload["config"]
    assert isinstance(config, dict)
    del config["chart_type"]

    response = client.post("/api/v1/charts/generate", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["error"]["code"] == "NBI-1001"
