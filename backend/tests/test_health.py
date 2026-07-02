"""Tests for the Health Platform endpoints.

Verifies all four health endpoints:
- GET /health       → Comprehensive system health
- GET /health/live  → Liveness probe
- GET /health/ready → Readiness probe
- GET /version      → Service version metadata
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_response_contains_status(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")

    def test_response_contains_service_name(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "service" in data
        assert data["service"] == "NexusBI Backend"

    def test_response_contains_environment(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "environment" in data

    def test_response_contains_timestamp(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "timestamp" in data

    def test_response_contains_uptime(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    def test_response_contains_checks_list(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "checks" in data
        assert isinstance(data["checks"], list)

    def test_postgres_check_present(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        check_names = [c["name"] for c in data["checks"]]
        assert "postgres" in check_names

    def test_root_health_endpoint(self, client: TestClient) -> None:
        """Health should also be accessible at the root path."""
        response = client.get("/health")
        assert response.status_code == 200


class TestLivenessEndpoint:
    """Tests for GET /api/v1/health/live."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200

    def test_response_status_is_ok(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        data = response.json()
        assert data["status"] == "ok"

    def test_response_contains_service(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        data = response.json()
        assert "service" in data

    def test_response_contains_timestamp(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        data = response.json()
        assert "timestamp" in data

    def test_root_live_endpoint(self, client: TestClient) -> None:
        """Liveness should also be accessible at /live."""
        response = client.get("/live")
        assert response.status_code == 200


class TestReadinessEndpoint:
    """Tests for GET /api/v1/health/ready."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200

    def test_response_contains_status(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ready")
        data = response.json()
        assert "status" in data

    def test_response_contains_checks_dict(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ready")
        data = response.json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    def test_postgres_check_in_readiness(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ready")
        data = response.json()
        assert "postgres" in data["checks"]

    def test_root_ready_endpoint(self, client: TestClient) -> None:
        """Readiness should also be accessible at /ready."""
        response = client.get("/ready")
        assert response.status_code == 200


class TestVersionEndpoint:
    """Tests for GET /api/v1/version."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        assert response.status_code == 200

    def test_response_contains_version(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        data = response.json()
        assert "version" in data

    def test_response_contains_service(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        data = response.json()
        assert "service" in data

    def test_response_contains_python_version(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        data = response.json()
        assert "python_version" in data

    def test_response_contains_environment(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        data = response.json()
        assert "environment" in data

    def test_response_contains_api_version(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        data = response.json()
        assert "api_version" in data
        assert data["api_version"] == "/api/v1"

    def test_response_contains_started_at(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        data = response.json()
        assert "started_at" in data
