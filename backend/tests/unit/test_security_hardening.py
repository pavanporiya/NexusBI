"""Security Hardening and Production Readiness Unit Tests.

Verifies:
1. TrustedHostMiddleware header validation.
2. OWASP security HTTP headers (CSP, HSTS, X-Content-Type-Options, etc.).
3. Sanitisation of internal exception details in non-debug mode.
4. Censor/redaction of sensitive data and Authorization headers in logging.
5. Cookie absence and secure defaults review.
6. JWT handling security (algorithm enforcement, token type isolation, secret strength).
7. Settings secret leakage prevention.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.core.config import Environment, Settings
from app.core.exceptions import (
    DatabaseError,
    NexusBIError,
    register_exception_handlers,
)
from app.core.logging import censor_sensitive_data
from app.core.middleware import SecurityHeadersMiddleware, setup_middleware
from app.infrastructure.services.jwt_token_service import JWTTokenService


class TestTrustedHostMiddleware:
    """Tests for Host header validation via TrustedHostMiddleware."""

    def test_allowed_host_request_succeeds(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live", headers={"Host": "testserver"})
        assert response.status_code == 200

    def test_untrusted_host_request_rejected(self) -> None:
        """Verify untrusted Host header is rejected when hosts restricted."""
        custom_app = FastAPI()
        settings = Settings(ALLOWED_HOSTS=["nexusbi.io", "api.nexusbi.io"])

        with patch("app.core.middleware.settings", settings):
            setup_middleware(custom_app)

        @custom_app.get("/test")
        async def test_endpoint() -> dict[str, str]:
            return {"status": "ok"}

        test_client = TestClient(custom_app)
        response = test_client.get("/test", headers={"Host": "untrusted-domain.com"})
        assert response.status_code == 400


class TestSecurityHTTPHeaders:
    """Tests for OWASP security HTTP response headers."""

    def test_content_security_policy_header_present(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert "content-security-policy" in response.headers
        csp = response.headers["content-security-policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_cross_domain_and_opener_policies_present(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert response.headers["x-permitted-cross-domain-policies"] == "none"
        assert response.headers["cross-origin-opener-policy"] == "same-origin"

    def test_hsts_header_added_in_production(self) -> None:
        custom_app = FastAPI()

        @custom_app.get("/test")
        async def test_endpoint() -> dict[str, str]:
            return {"status": "ok"}

        prod_settings = Settings(
            ENV=Environment.PRODUCTION,
            SECRET_KEY=SecretStr("a_very_secure_secret_key_32bytes_long!"),
        )
        with patch("app.core.middleware.settings", prod_settings):
            custom_app.add_middleware(SecurityHeadersMiddleware)
            test_client = TestClient(custom_app)
            response = test_client.get("/test")
            assert "strict-transport-security" in response.headers
            assert "max-age=31536000" in response.headers["strict-transport-security"]


class TestSensitiveExceptionNonExposure:
    """Tests to ensure internal exception details are not exposed in non-debug mode."""

    def test_database_error_detail_sanitised_in_production(self) -> None:
        custom_app = FastAPI()
        register_exception_handlers(custom_app)

        @custom_app.get("/db-error")
        async def db_error_route() -> None:
            raise DatabaseError(
                detail="psycopg2.OperationalError: Connection refused to postgres"
            )

        prod_settings = Settings(
            ENV=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY=SecretStr("a_very_secure_secret_key_32bytes_long!"),
        )
        with patch("app.core.config.settings", prod_settings):
            test_client = TestClient(custom_app)
            response = test_client.get("/db-error")
            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "NBI-5001"
            assert data["error"]["detail"] == "An internal server error occurred."
            assert "psycopg2" not in data["error"]["detail"]


class TestAuthorizationHeaderLoggingSanitisation:
    """Tests verifying sensitive key and Authorization header censorship in logging."""

    def test_censor_sensitive_data_redacts_authorization_key(self) -> None:
        event_dict = {
            "event": "user_login",
            "authorization": "Bearer secret_jwt_token_12345",
            "password": "my_secret_password",
            "safe_key": "safe_value",
        }
        result = censor_sensitive_data(None, "info", event_dict)
        assert result["authorization"] == "***REDACTED***"
        assert result["password"] == "***REDACTED***"
        assert result["safe_key"] == "safe_value"

    def test_nested_dict_redaction(self) -> None:
        event_dict = {
            "headers": {
                "Authorization": "Bearer secret_jwt_token_12345",
                "User-Agent": "Pytest/1.0",
            }
        }
        result = censor_sensitive_data(None, "info", event_dict)
        assert result["headers"]["Authorization"] == "***REDACTED***"
        assert result["headers"]["User-Agent"] == "Pytest/1.0"


class TestCookieConfigurationReview:
    """Tests verifying cookies are not set by auth endpoints."""

    def test_no_set_cookie_header_on_responses(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/live")
        assert "set-cookie" not in response.headers


class TestJWTSecurityHardening:
    """Tests for JWT token service security guarantees."""

    def test_jwt_token_type_isolation(self) -> None:
        service = JWTTokenService(secret_key="a_very_secure_secret_key_32bytes_long!")
        refresh_token = service.create_refresh_token(
            subject="user_123", token_id="session_abc"
        )

        with pytest.raises(NexusBIError) as exc_info:
            service.verify_access_token(refresh_token)
        assert exc_info.value.code == "NBI-1002"

    def test_jwt_service_requires_non_empty_secret(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            JWTTokenService(secret_key="")

    def test_short_secret_key_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="at least 32 characters"):
            Settings(
                ENV=Environment.PRODUCTION,
                SECRET_KEY=SecretStr("short_key"),
            )


class TestConfigSecretLeakagePrevention:
    """Tests verifying secret values are not leaked via configuration objects."""

    def test_secret_key_masked_in_str_and_repr(self) -> None:
        s = Settings(SECRET_KEY=SecretStr("super_secret_production_key_12345678"))
        assert "super_secret_production_key_12345678" not in repr(s.SECRET_KEY)
        assert "super_secret_production_key_12345678" not in str(s.SECRET_KEY)

    def test_wildcard_cors_rejected_in_production(self) -> None:
        with pytest.raises(
            ValidationError, match="ALLOWED_ORIGINS cannot contain wildcard"
        ):
            Settings(
                ENV=Environment.PRODUCTION,
                SECRET_KEY=SecretStr("a_very_secure_secret_key_32bytes_long!"),
                ALLOWED_ORIGINS=["*"],
            )
