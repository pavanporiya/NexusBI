"""Tests for the Exception Framework.

Verifies the exception hierarchy, error code assignments, and
global exception handler behavior.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestExceptionHierarchy:
    """Tests for the exception class hierarchy."""

    def test_nexusbi_error_is_exception(self) -> None:
        from app.core.exceptions import NexusBIError

        exc = NexusBIError(code="NBI-9999", message="test", status_code=500)
        assert isinstance(exc, Exception)

    def test_validation_error_code(self) -> None:
        from app.core.exceptions import ValidationError

        exc = ValidationError()
        assert exc.code == "NBI-1001"
        assert exc.status_code == 400

    def test_authentication_error_code(self) -> None:
        from app.core.exceptions import AuthenticationError

        exc = AuthenticationError()
        assert exc.code == "NBI-1002"
        assert exc.status_code == 401

    def test_authorization_error_code(self) -> None:
        from app.core.exceptions import AuthorizationError

        exc = AuthorizationError()
        assert exc.code == "NBI-1003"
        assert exc.status_code == 403

    def test_ai_provider_error_code(self) -> None:
        from app.core.exceptions import AIProviderError

        exc = AIProviderError()
        assert exc.code == "NBI-2001"
        assert exc.status_code == 504

    def test_sql_validation_error_code(self) -> None:
        from app.core.exceptions import SQLValidationError

        exc = SQLValidationError()
        assert exc.code == "NBI-2002"
        assert exc.status_code == 422

    def test_warehouse_query_error_code(self) -> None:
        from app.core.exceptions import WarehouseQueryError

        exc = WarehouseQueryError()
        assert exc.code == "NBI-3001"
        assert exc.status_code == 500

    def test_warehouse_timeout_error_code(self) -> None:
        from app.core.exceptions import WarehouseTimeoutError

        exc = WarehouseTimeoutError()
        assert exc.code == "NBI-3002"
        assert exc.status_code == 504

    def test_entity_not_found_error_code(self) -> None:
        from app.core.exceptions import EntityNotFoundError

        exc = EntityNotFoundError("User", "123")
        assert exc.code == "NBI-4001"
        assert exc.status_code == 404

    def test_duplicate_entity_error_code(self) -> None:
        from app.core.exceptions import DuplicateEntityError

        exc = DuplicateEntityError("Dashboard", "my-dashboard")
        assert exc.code == "NBI-4002"
        assert exc.status_code == 409

    def test_database_error_code(self) -> None:
        from app.core.exceptions import DatabaseError

        exc = DatabaseError()
        assert exc.code == "NBI-5001"
        assert exc.status_code == 500

    def test_rate_limit_exceeded_error_code(self) -> None:
        from app.core.exceptions import RateLimitExceededError

        exc = RateLimitExceededError()
        assert exc.code == "NBI-5004"
        assert exc.status_code == 429


class TestExceptionInheritance:
    """Tests that subclasses properly inherit from NexusBIError."""

    def test_token_expired_is_authentication_error(self) -> None:
        from app.core.exceptions import AuthenticationError, TokenExpiredError

        exc = TokenExpiredError()
        assert isinstance(exc, AuthenticationError)

    def test_unsafe_sql_is_sql_validation_error(self) -> None:
        from app.core.exceptions import SQLValidationError, UnsafeSQLError

        exc = UnsafeSQLError("DROP")
        assert isinstance(exc, SQLValidationError)

    def test_ai_timeout_is_ai_provider_error(self) -> None:
        from app.core.exceptions import AIProviderError, AITimeoutError

        exc = AITimeoutError("anthropic", 15)
        assert isinstance(exc, AIProviderError)

    def test_insufficient_role_is_authorization_error(self) -> None:
        from app.core.exceptions import AuthorizationError, InsufficientRoleError

        exc = InsufficientRoleError("admin")
        assert isinstance(exc, AuthorizationError)


class TestExceptionHandlers:
    """Tests for global exception handler responses."""

    def test_404_returns_standard_error_envelope(self, client: TestClient) -> None:
        response = client.get("/nonexistent/path")
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "timestamp" in data["error"]

    def test_error_envelope_format(self, client: TestClient) -> None:
        """Verify the error response matches the API blueprint schema."""
        response = client.get("/nonexistent/path")
        error = response.json()["error"]
        assert isinstance(error["code"], str)
        assert error["code"].startswith("NBI-")
        assert isinstance(error["message"], str)
        assert isinstance(error["timestamp"], str)
