"""API tests for Connector Management endpoints."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.dependencies import get_connector_service
from app.application.services.connector_service import (
    ConnectorDiscoveryResult,
    ConnectorService,
)
from app.domain.connectors.types import ColumnMetadata


@pytest.fixture
def mock_connector_service() -> MagicMock:
    service = MagicMock(spec=ConnectorService)
    service.test_connection.return_value = True
    service.discover.return_value = ConnectorDiscoveryResult(
        schemas=["public"],
        tables=["users"],
        columns=[
            ColumnMetadata(name="id", type="integer", nullable=False, primary_key=True),
            ColumnMetadata(
                name="email", type="text", nullable=False, primary_key=False
            ),
        ],
    )
    service.list_schemas.return_value = ["public"]
    service.list_tables.return_value = ["users"]
    service.list_columns.return_value = [
        ColumnMetadata(name="id", type="integer", nullable=False, primary_key=True),
    ]
    return service


@pytest.fixture
def client(app: FastAPI, mock_connector_service: MagicMock) -> Generator[TestClient]:
    app.dependency_overrides[get_connector_service] = lambda: mock_connector_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_post_connector_test_succeeds(
    client: TestClient, mock_connector_service: MagicMock
) -> None:
    response = client.post(
        "/api/v1/connectors/test",
        json={
            "connector_type": "postgresql",
            "id": "test-connector",
            "name": "Test Connector",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "user",
            "password": "pass",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "succeeded" in data["message"].lower()
    mock_connector_service.test_connection.assert_called_once()


def test_post_connector_discover_returns_metadata(
    client: TestClient, mock_connector_service: MagicMock
) -> None:
    response = client.post(
        "/api/v1/connectors/discover",
        json={
            "connector_type": "postgresql",
            "id": "test-connector",
            "name": "Test Connector",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "user",
            "password": "pass",
            "table_name": "users",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["schemas"] == ["public"]
    assert data["tables"] == ["users"]
    assert data["columns"][0]["name"] == "id"
    mock_connector_service.discover.assert_called_once()


def test_get_connector_schemas_accepts_query_params(
    client: TestClient, mock_connector_service: MagicMock
) -> None:
    response = client.get(
        "/api/v1/connectors/schemas?connector_type=postgresql&host=localhost&database=testdb&username=user&password=pass"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == ["public"]
    mock_connector_service.list_schemas.assert_called_once()


def test_get_connector_columns_requires_table_name(
    client: TestClient, mock_connector_service: MagicMock
) -> None:
    response = client.get(
        "/api/v1/connectors/columns?connector_type=postgresql&host=localhost&database=testdb&username=user&password=pass&table_name=users"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["name"] == "id"
    assert data[0]["primary_key"] is True
    mock_connector_service.list_columns.assert_called_once()


def test_post_connector_test_fails_validation_when_missing_fields(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/connectors/test",
        json={"id": "bad-connector", "name": "Bad Connector"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
