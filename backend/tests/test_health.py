"""Tests for the Health Platform endpoints.

Verifies health endpoints:
- GET /health       → Comprehensive system health report
- GET /health/live  → Liveness probe
- GET /health/ready → Readiness probe
- GET /version      → Service version metadata
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.application.dto.health_dto import ComponentHealth, HealthStatus


class TestHealthEndpoint:
    """Tests for GET /api/v1/health and GET /health."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_response_contains_status(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")

    def test_response_contains_version(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"

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

    def test_postgres_and_redis_checks_present(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        check_names = [c["name"] for c in data["checks"]]
        assert "postgres" in check_names
        assert "redis" in check_names

    def test_root_health_endpoint(self, client: TestClient) -> None:
        """Health should also be accessible at the root path."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_db_failure(
        self, client: TestClient, mock_db_session: MagicMock
    ) -> None:
        mock_db_session.execute.side_effect = OperationalError(
            "SELECT 1", {}, Exception("DB failure")
        )
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        pg_check = next(c for c in data["checks"] if c["name"] == "postgres")
        assert pg_check["status"] == "unhealthy"


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
        """Liveness should also be accessible at /live and /health/live."""
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        response2 = client.get("/health/live")
        assert response2.status_code == 200
        assert response2.json()["status"] == "ok"


class TestReadinessEndpoint:
    """Tests for GET /api/v1/health/ready."""

    def test_returns_200_and_success(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")

    def test_response_contains_checks_dict(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ready")
        data = response.json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)
        assert "postgres" in data["checks"]
        assert "redis" in data["checks"]

    def test_root_ready_endpoint(self, client: TestClient) -> None:
        """Readiness should also be accessible at /ready and /health/ready."""
        response = client.get("/ready")
        assert response.status_code == 200

        response2 = client.get("/health/ready")
        assert response2.status_code == 200

    def test_readiness_db_failure(
        self, client: TestClient, mock_db_session: MagicMock
    ) -> None:
        """Readiness probe should report 503 on DB failure without crashing."""
        mock_db_session.execute.side_effect = OperationalError(
            "SELECT 1", {}, Exception("DB Connection Refused")
        )
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["postgres"] == "unhealthy"

    def test_readiness_redis_unavailable(self, client: TestClient) -> None:
        """Readiness probe should handle redis unavailability gracefully."""
        with patch("app.api.health._check_redis") as mock_redis_check:
            mock_redis_check.return_value = ComponentHealth(
                name="redis",
                status=HealthStatus.UNAVAILABLE,
                detail="Connection refused",
            )
            response = client.get("/api/v1/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["checks"]["redis"] == "unavailable"


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
