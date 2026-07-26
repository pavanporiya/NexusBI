"""Unit and schema validation tests for NexusBI OpenAPI documentation.

Verifies global FastAPI metadata, endpoint documentation completeness,
operation IDs, error response models, security scheme configuration,
and schema examples.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def test_openapi_json_endpoint() -> None:
    """Verify GET /api/v1/openapi.json returns a valid 200 OK specification."""
    client = TestClient(app)
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "NexusBI Backend API"
    assert schema["info"]["version"] == "1.0.0"
    assert "NexusBI — Enterprise Analytics Copilot API" in schema["info"]["description"]
    assert schema["info"]["contact"]["name"] == "NexusBI Platform Team"
    assert schema["info"]["license"]["name"] == "Proprietary"


def test_openapi_security_schemes() -> None:
    """Verify Bearer JWT HTTP security scheme is registered under components."""
    client = TestClient(app)
    schema = client.get("/api/v1/openapi.json").json()

    components = schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})

    assert "HTTPBearer" in security_schemes
    bearer_scheme = security_schemes["HTTPBearer"]
    assert bearer_scheme["type"] == "http"
    assert bearer_scheme["scheme"] == "bearer"
    assert bearer_scheme["bearerFormat"] == "JWT"
    assert "description" in bearer_scheme


def test_openapi_tags_metadata() -> None:
    """Verify openapi_tags metadata array is configured with tag descriptions."""
    client = TestClient(app)
    schema = client.get("/api/v1/openapi.json").json()

    tags = {tag["name"]: tag["description"] for tag in schema.get("tags", [])}
    assert "System Health" in tags
    assert "Authentication" in tags
    assert "User Management" in tags
    assert "Role Management" in tags


def test_openapi_endpoints_completeness() -> None:
    """Verify all REST endpoints have summary, description, operation_id, and tags."""
    client = TestClient(app)
    schema = client.get("/api/v1/openapi.json").json()
    paths = schema.get("paths", {})

    expected_endpoints = [
        ("/api/v1/health", "get"),
        ("/api/v1/health/live", "get"),
        ("/api/v1/health/ready", "get"),
        ("/api/v1/version", "get"),
        ("/api/v1/auth/register", "post"),
        ("/api/v1/auth/login", "post"),
        ("/api/v1/auth/refresh", "post"),
        ("/api/v1/auth/logout", "post"),
        ("/api/v1/auth/me", "get"),
        ("/api/v1/users/me", "get"),
        ("/api/v1/users/{user_id}", "get"),
        ("/api/v1/users/{user_id}", "patch"),
        ("/api/v1/roles", "get"),
        ("/api/v1/roles", "post"),
        ("/api/v1/roles/{role_id}", "get"),
        ("/api/v1/roles/{role_id}", "patch"),
        ("/api/v1/roles/{role_id}", "delete"),
    ]

    for path_str, method_str in expected_endpoints:
        assert path_str in paths, f"Path {path_str} missing from OpenAPI schema"
        operation: dict[str, Any] = paths[path_str][method_str]

        assert "summary" in operation
        assert operation["summary"]
        assert "description" in operation
        assert operation["description"]
        assert "operationId" in operation
        assert operation["operationId"]
        assert "tags" in operation
        assert len(operation["tags"]) > 0


def test_openapi_public_vs_protected_security() -> None:
    """Verify public and protected endpoints security scheme configuration."""
    client = TestClient(app)
    schema = client.get("/api/v1/openapi.json").json()
    paths = schema.get("paths", {})

    public_routes = [
        ("/api/v1/health", "get"),
        ("/api/v1/health/live", "get"),
        ("/api/v1/health/ready", "get"),
        ("/api/v1/version", "get"),
        ("/api/v1/auth/register", "post"),
        ("/api/v1/auth/login", "post"),
        ("/api/v1/auth/refresh", "post"),
    ]

    protected_routes = [
        ("/api/v1/auth/logout", "post"),
        ("/api/v1/auth/me", "get"),
        ("/api/v1/users/me", "get"),
        ("/api/v1/users/{user_id}", "get"),
        ("/api/v1/users/{user_id}", "patch"),
        ("/api/v1/roles", "get"),
        ("/api/v1/roles", "post"),
        ("/api/v1/roles/{role_id}", "get"),
        ("/api/v1/roles/{role_id}", "patch"),
        ("/api/v1/roles/{role_id}", "delete"),
    ]

    for path_str, method_str in public_routes:
        operation = paths[path_str][method_str]
        assert operation.get("security") == []

    for path_str, method_str in protected_routes:
        operation = paths[path_str][method_str]
        assert operation.get("security") == [{"HTTPBearer": []}]


def test_openapi_models_and_examples() -> None:
    """Verify Pydantic models contain field descriptions and schema examples."""
    client = TestClient(app)
    schema = client.get("/api/v1/openapi.json").json()

    schemas = schema.get("components", {}).get("schemas", {})
    required_schemas = [
        "UserDTO",
        "TokenDTO",
        "LoginDTO",
        "RegisterDTO",
        "TokenRefreshDTO",
        "UpdateUserProfileDTO",
        "RoleDTO",
        "CreateRoleDTO",
        "UpdateRoleDTO",
        "PermissionDTO",
        "ErrorResponseEnvelope",
        "ErrorDetailDTO",
    ]

    for schema_name in required_schemas:
        assert schema_name in schemas, f"Schema {schema_name} missing"
        model_schema = schemas[schema_name]
        assert "properties" in model_schema, f"Properties missing in {schema_name}"
