"""Tests for the Middleware Stack.

Verifies request ID injection, security headers, response timing,
and logging middleware behavior.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestRequestIDMiddleware:
    """Tests for the Request ID middleware."""

    def test_response_contains_request_id_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert "x-request-id" in response.headers

    def test_request_id_is_non_empty(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        request_id = response.headers["x-request-id"]
        assert len(request_id) > 0

    def test_client_provided_request_id_is_propagated(self, client: TestClient) -> None:
        custom_id = "test-trace-id-12345"
        response = client.get(
            "/api/v1/health/live",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["x-request-id"] == custom_id

    def test_client_provided_trace_id_is_propagated(self, client: TestClient) -> None:
        custom_id = "trace-from-gateway-67890"
        response = client.get(
            "/api/v1/health/live",
            headers={"X-Trace-ID": custom_id},
        )
        assert response.headers["x-request-id"] == custom_id


class TestSecurityHeadersMiddleware:
    """Tests for the Security Headers middleware."""

    def test_x_content_type_options_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_x_frame_options_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert response.headers["x-frame-options"] == "DENY"

    def test_x_xss_protection_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert response.headers["x-xss-protection"] == "1; mode=block"

    def test_referrer_policy_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert "permissions-policy" in response.headers

    def test_cache_control_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert "no-store" in response.headers["cache-control"]


class TestTimingMiddleware:
    """Tests for the Timing middleware."""

    def test_server_timing_header_present(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert "server-timing" in response.headers

    def test_server_timing_contains_total(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        timing = response.headers["server-timing"]
        assert "total;dur=" in timing

    def test_response_time_header_present(self, client: TestClient) -> None:
        response = client.get("/api/v1/version")
        assert "x-response-time" in response.headers
