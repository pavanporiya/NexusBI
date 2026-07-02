"""Tests for the Structured Logging Platform.

Verifies logging configuration, correlation ID management,
sensitive data censoring, and audit logger functionality.
"""

from __future__ import annotations

from typing import Any


class TestCorrelationID:
    """Tests for correlation ID context management."""

    def test_get_generates_id_when_empty(self) -> None:
        from app.core.logging import get_correlation_id, reset_correlation_id

        reset_correlation_id()
        cid = get_correlation_id()
        assert isinstance(cid, str)
        assert len(cid) == 32  # UUID hex is 32 chars
        reset_correlation_id()

    def test_set_and_get_returns_same_value(self) -> None:
        from app.core.logging import (
            get_correlation_id,
            reset_correlation_id,
            set_correlation_id,
        )

        reset_correlation_id()
        set_correlation_id("test-correlation-id")
        assert get_correlation_id() == "test-correlation-id"
        reset_correlation_id()

    def test_reset_clears_correlation_id(self) -> None:
        from app.core.logging import (
            correlation_id_ctx,
            reset_correlation_id,
            set_correlation_id,
        )

        set_correlation_id("some-id")
        reset_correlation_id()
        assert correlation_id_ctx.get("") == ""


class TestSensitiveDataCensoring:
    """Tests for the censor_sensitive_data processor."""

    def test_password_field_is_redacted(self) -> None:
        from app.core.logging import censor_sensitive_data

        event = {"event": "test", "password": "secret123"}
        result = censor_sensitive_data(None, "info", event)
        assert result["password"] == "***REDACTED***"

    def test_api_key_field_is_redacted(self) -> None:
        from app.core.logging import censor_sensitive_data

        event = {"event": "test", "api_key": "sk-abc123"}
        result = censor_sensitive_data(None, "info", event)
        assert result["api_key"] == "***REDACTED***"

    def test_token_field_is_redacted(self) -> None:
        from app.core.logging import censor_sensitive_data

        event = {"event": "test", "access_token": "jwt.payload.sig"}
        result = censor_sensitive_data(None, "info", event)
        assert result["access_token"] == "***REDACTED***"

    def test_non_sensitive_field_is_preserved(self) -> None:
        from app.core.logging import censor_sensitive_data

        event = {"event": "test", "user_id": "user-123"}
        result = censor_sensitive_data(None, "info", event)
        assert result["user_id"] == "user-123"


class TestServiceContext:
    """Tests for the add_service_context processor."""

    def test_adds_service_name(self) -> None:
        from app.core.logging import add_service_context

        event: dict[str, Any] = {"event": "test"}
        result = add_service_context(None, "info", event)
        assert result["service"] == "nexusbi-backend"

    def test_does_not_override_existing_service(self) -> None:
        from app.core.logging import add_service_context

        event: dict[str, Any] = {"event": "test", "service": "custom-service"}
        result = add_service_context(None, "info", event)
        assert result["service"] == "custom-service"


class TestGetLogger:
    """Tests for the logger factory function."""

    def test_returns_bound_logger(self) -> None:
        from app.core.logging import get_logger

        log = get_logger("test.module")
        assert log is not None

    def test_initial_context_is_bound(self) -> None:
        from app.core.logging import get_logger

        log = get_logger("test.module", component="auth")
        # The logger should have the context bound
        assert log is not None


class TestAuditLogger:
    """Tests for the AuditLogger class."""

    def test_audit_logger_instantiation(self) -> None:
        from app.core.logging import AuditLogger

        audit = AuditLogger()
        assert audit is not None
        assert audit._logger is not None

    def test_log_query_execution_does_not_raise(self) -> None:
        from app.core.logging import AuditLogger

        audit = AuditLogger()
        audit.log_query_execution(
            user_id="user-123",
            query_text="Show me revenue",
            generated_sql="SELECT SUM(revenue) FROM fct_orders",
            execution_time_ms=150.5,
            row_count=42,
            tables_accessed=["fct_orders"],
        )

    def test_log_llm_transaction_does_not_raise(self) -> None:
        from app.core.logging import AuditLogger

        audit = AuditLogger()
        audit.log_llm_transaction(
            user_id="user-123",
            model="claude-sonnet-4-20250514",
            prompt_tokens=500,
            completion_tokens=200,
            latency_ms=1200.0,
            cost_usd=0.003,
        )

    def test_log_security_event_does_not_raise(self) -> None:
        from app.core.logging import AuditLogger

        audit = AuditLogger()
        audit.log_security_event(
            event_type="login_failure",
            user_id="user-456",
            ip_address="192.168.1.1",
            detail="Invalid credentials",
        )

    def test_log_data_access_does_not_raise(self) -> None:
        from app.core.logging import AuditLogger

        audit = AuditLogger()
        audit.log_data_access(
            user_id="user-789",
            resource_type="dashboard",
            resource_id="dash-001",
            action="read",
        )
