"""Tests for Production Readiness Module 1: Structured Logging.

Verifies:
- Request ID creation
- Request ID propagation
- Structured logging (request_id, method, path, status, duration)
- Sensitive data censoring (passwords, tokens, secrets, authorization)
- Exception logging (request_id, exception_type, message)
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import NexusBIError, register_exception_handlers
from app.core.logging import (
    add_correlation_id,
    censor_sensitive_data,
    get_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)
from app.core.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from app.main import create_app


def _parse_log_entry(raw: str) -> dict[str, Any]:
    """Parse JSON log string emitted to stdout or caplog."""
    data: dict[str, Any] = json.loads(raw)
    event_val = data.get("event")
    if isinstance(event_val, str) and event_val.startswith("{"):
        inner: dict[str, Any] = json.loads(event_val)
        return inner
    return data


def _get_captured_log_entries(
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> list[dict[str, Any]]:
    """Gather and parse structured JSON log entries from caplog and capsys."""
    entries: list[dict[str, Any]] = []

    # 1. Inspect caplog records
    for record in caplog.records:
        try:
            entries.append(_parse_log_entry(record.getMessage()))
        except (json.JSONDecodeError, TypeError):
            pass

    # 2. Inspect capsys stdout
    captured_stdout = capsys.readouterr().out
    for line in captured_stdout.strip().splitlines():
        try:
            entries.append(_parse_log_entry(line))
        except (json.JSONDecodeError, TypeError):
            pass

    return entries


class TestRequestIDCreationAndPropagation:
    """Tests for Request ID creation and propagation."""

    def test_request_id_created_when_missing(self, client: TestClient) -> None:
        """Verify that a request ID is automatically generated if omitted."""
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        req_id = response.headers["x-request-id"]
        assert isinstance(req_id, str)
        assert len(req_id) > 0

    def test_request_id_propagated_from_header(self, client: TestClient) -> None:
        """Verify client-supplied X-Request-ID is preserved and propagated."""
        custom_id = "req-id-uuid-test-12345"
        response = client.get("/api/v1/version", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers["x-request-id"] == custom_id

    def test_trace_id_propagated_from_header(self, client: TestClient) -> None:
        """Verify client-supplied X-Trace-ID is preserved and propagated."""
        custom_trace_id = "trace-id-gateway-67890"
        response = client.get(
            "/api/v1/version", headers={"X-Trace-ID": custom_trace_id}
        )
        assert response.status_code == 200
        assert response.headers["x-request-id"] == custom_trace_id

    def test_correlation_id_context_vars(self) -> None:
        """Verify correlation ID context set and reset helpers."""
        reset_correlation_id()
        cid1 = get_correlation_id()
        assert len(cid1) == 32  # UUID hex length
        set_correlation_id("manual-id-999")
        assert get_correlation_id() == "manual-id-999"
        reset_correlation_id()


class TestStructuredLogging:
    """Tests for structured logging attributes and sensitive field redaction."""

    def test_add_correlation_id_processor(self) -> None:
        """Verify add_correlation_id injects correlation_id and request_id."""
        reset_correlation_id()
        set_correlation_id("test-corr-id")
        event: dict[str, Any] = {"event": "test_event"}
        result = add_correlation_id(None, "info", event)
        assert result["correlation_id"] == "test-corr-id"
        assert result["request_id"] == "test-corr-id"
        reset_correlation_id()

    def test_censor_sensitive_data_processor(self) -> None:
        """Verify passwords, tokens, secrets, and auth headers are redacted."""
        event: dict[str, Any] = {
            "event": "login_attempt",
            "password": "my_secret_password",
            "access_token": "bearer_xyz_123",
            "secret_key": "topsecret",
            "authorization": "Bearer token123",
            "nested": {
                "user_password": "nested_password",
                "auth_header": "Bearer secret_jwt",
                "normal_field": "safe_value",
            },
        }
        result = censor_sensitive_data(None, "info", event)
        assert result["password"] == "***REDACTED***"
        assert result["access_token"] == "***REDACTED***"
        assert result["secret_key"] == "***REDACTED***"
        assert result["authorization"] == "***REDACTED***"
        assert result["nested"]["user_password"] == "***REDACTED***"
        assert result["nested"]["auth_header"] == "***REDACTED***"
        assert result["nested"]["normal_field"] == "safe_value"

    def test_request_logging_middleware_output(
        self, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify request logging includes request_id, method, status, duration."""
        app = create_app()
        test_client = TestClient(app)

        with caplog.at_level("INFO"):
            resp = test_client.get(
                "/api/v1/version", headers={"X-Request-ID": "req-struct-test"}
            )
            assert resp.status_code == 200

        entries = _get_captured_log_entries(caplog, capsys)
        completed_logs = [e for e in entries if e.get("event") == "Request completed"]
        assert len(completed_logs) >= 1
        log_entry = completed_logs[0]

        assert log_entry["request_id"] == "req-struct-test"
        assert log_entry["method"] == "GET"
        assert log_entry["path"] == "/api/v1/version"
        assert log_entry["status"] == 200
        assert "duration" in log_entry
        assert isinstance(log_entry["duration"], float)


class TestExceptionLogging:
    """Tests for exception logging attributes."""

    def test_nexusbi_exception_logging(
        self, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify exception logging includes request_id, exception_type, message."""
        test_app = FastAPI()
        register_exception_handlers(test_app)
        test_app.add_middleware(RequestLoggingMiddleware)
        test_app.add_middleware(RequestIDMiddleware)

        @test_app.get("/trigger-error-direct")
        async def error_route() -> None:
            raise NexusBIError(
                code="NBI-4001",
                message="Resource missing",
                status_code=404,
                detail="The requested item was not found.",
            )

        with caplog.at_level("ERROR"):
            client = TestClient(test_app)
            resp = client.get(
                "/trigger-error-direct", headers={"X-Request-ID": "req-exc-test"}
            )
            assert resp.status_code == 404

        entries = _get_captured_log_entries(caplog, capsys)
        error_logs = [e for e in entries if e.get("event") == "Application error"]
        assert len(error_logs) >= 1
        log_entry = error_logs[0]

        assert log_entry["request_id"] == "req-exc-test"
        assert log_entry["exception_type"] == "NexusBIError"
        assert log_entry["message"] == "Resource missing"
        assert log_entry["status"] == 404
        assert log_entry["method"] == "GET"
        assert log_entry["path"] == "/trigger-error-direct"

    def test_unhandled_exception_logging(
        self, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify unhandled exception logging attributes in middleware."""
        test_app = FastAPI()
        test_app.add_middleware(RequestLoggingMiddleware)
        test_app.add_middleware(RequestIDMiddleware)

        @test_app.get("/trigger-unhandled")
        async def unhandled_route() -> None:
            raise ValueError("Something unexpected broke")

        with caplog.at_level("ERROR"):
            client = TestClient(test_app, raise_server_exceptions=False)
            resp = client.get(
                "/trigger-unhandled",
                headers={"X-Request-ID": "req-unhandled-test"},
            )
            assert resp.status_code == 500

        entries = _get_captured_log_entries(caplog, capsys)
        unhandled_logs = [
            e
            for e in entries
            if e.get("event")
            in ("Request failed with exception", "Unhandled server exception")
        ]
        assert len(unhandled_logs) >= 1
        log_entry = unhandled_logs[0]

        assert log_entry["request_id"] == "req-unhandled-test"
        assert log_entry["exception_type"] == "ValueError"
        assert log_entry["message"] == "Something unexpected broke"
        assert log_entry["status"] == 500
        assert log_entry["method"] == "GET"
        assert log_entry["path"] == "/trigger-unhandled"
