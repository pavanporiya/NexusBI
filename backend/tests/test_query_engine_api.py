"""Comprehensive REST API tests for Universal Query Engine endpoints."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_authorization_service,
    get_current_user,
    get_query_service,
)
from app.application.services.interfaces import IAuthorizationService
from app.application.services.query_service import QueryService
from app.core.exceptions import InvalidQueryError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.value_objects.query import (
    QueryColumn,
    QueryMetadata,
    QueryResult,
    QueryStatistics,
)
from app.main import app


@pytest.fixture
def sample_user() -> User:
    """Authenticated user with datasets:read permissions."""
    perm_read = Permission(
        id="p-ds-r", resource="datasets", action="read", description=""
    )
    role = Role(id="r-1", name="QueryUser", permissions=[perm_read])
    return User(id="usr-query-001", email="query-user@nexusbi.io", roles=[role])


@pytest.fixture
def mock_auth_service() -> MagicMock:
    auth_svc = MagicMock(spec=IAuthorizationService)
    auth_svc.has_permission.return_value = True
    auth_svc.has_any_permission.return_value = True
    auth_svc.has_all_permissions.return_value = True
    auth_svc.can_access.return_value = True
    auth_svc.get_user_permissions.return_value = {"datasets:read"}
    auth_svc.get_user_roles.return_value = {"QueryUser"}
    return auth_svc


@pytest.fixture
def mock_query_service() -> MagicMock:
    service = MagicMock(spec=QueryService)

    sample_metadata = QueryMetadata(
        statistics=QueryStatistics(query_plan="SELECT 1", rows_scanned=1),
        execution_time=0.005,
        row_count=1,
        columns=[QueryColumn(name="val", type="integer")],
    )
    sample_result = QueryResult(
        rows=[{"val": 1}],
        columns=[QueryColumn(name="val", type="integer")],
        column_types={"val": "integer"},
        execution_time=0.005,
        row_count=1,
        metadata=sample_metadata,
    )

    service.validate.return_value = True
    service.execute.return_value = sample_result
    service.explain.return_value = sample_metadata
    service.preview_dataset.return_value = sample_result
    return service


@pytest.fixture
def client(
    sample_user: User,
    mock_auth_service: MagicMock,
    mock_query_service: MagicMock,
) -> Generator[TestClient]:
    app.dependency_overrides[get_current_user] = lambda: sample_user
    app.dependency_overrides[get_authorization_service] = lambda: mock_auth_service
    app.dependency_overrides[get_query_service] = lambda: mock_query_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_api_validate_query_success(
    client: TestClient, mock_query_service: MagicMock
) -> None:
    response = client.post(
        "/api/v1/query/validate",
        json={"sql": "SELECT 1 AS val", "parameters": {}},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is True
    assert "Query is valid" in data["message"]
    mock_query_service.validate.assert_called_once()


def test_api_validate_query_invalid(
    client: TestClient, mock_query_service: MagicMock
) -> None:
    mock_query_service.validate.side_effect = InvalidQueryError("DROP is prohibited")
    response = client.post(
        "/api/v1/query/validate",
        json={"sql": "DROP TABLE users", "parameters": {}},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"]["code"] == "NBI-2002"
    assert "DROP is prohibited" in data["error"]["detail"]


def test_api_execute_query_success(
    client: TestClient, mock_query_service: MagicMock
) -> None:
    response = client.post(
        "/api/v1/query/execute",
        json={"sql": "SELECT * FROM sales", "limit": 10, "offset": 0},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["row_count"] == 1
    assert len(data["rows"]) == 1
    assert data["rows"][0]["val"] == 1
    mock_query_service.execute.assert_called_once()


def test_api_explain_query_success(
    client: TestClient, mock_query_service: MagicMock
) -> None:
    response = client.post(
        "/api/v1/query/explain",
        json={"sql": "SELECT * FROM sales"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "statistics" in data
    assert data["statistics"]["query_plan"] == "SELECT 1"
    mock_query_service.explain.assert_called_once()


def test_api_preview_dataset_success(
    client: TestClient, mock_query_service: MagicMock
) -> None:
    response = client.get(
        "/api/v1/query/preview-dataset/ds-123?limit=5&offset=0",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["row_count"] == 1
    mock_query_service.preview_dataset.assert_called_once_with(
        dataset_id="ds-123",
        limit=5,
        offset=0,
    )
