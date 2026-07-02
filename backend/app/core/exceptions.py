"""NexusBI Exception Framework.

Defines a hierarchical exception taxonomy covering validation, HTTP,
domain, and infrastructure error categories. Each exception carries a
structured NBI-XXXX error code for consistent API error envelopes.

Architecture Reference:
- phase2_3_api_service_blueprint.md Section 5 (Error Handling Blueprint)
- Error Code Registry: config/error_codes.yaml
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Error Response Builder
# ---------------------------------------------------------------------------


def _build_error_response(
    status_code: int,
    code: str,
    message: str,
    detail: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Build a standardised JSON error response envelope.

    Schema follows phase2_3_api_service_blueprint.md Section 5.1.
    """
    payload: dict[str, Any] = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "detail": detail or message,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
    if errors:
        payload["error"]["errors"] = errors
    return JSONResponse(status_code=status_code, content=payload)


# ═══════════════════════════════════════════════════════════════════════════
# BASE EXCEPTION
# ═══════════════════════════════════════════════════════════════════════════


class NexusBIError(Exception):
    """Root exception for all NexusBI application errors.

    Every custom exception in the system inherits from this class,
    ensuring uniform error code assignment and response serialisation.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION EXCEPTIONS (NBI-1001)
# ═══════════════════════════════════════════════════════════════════════════


class ValidationError(NexusBIError):
    """Request validation failed — missing parameters or bad formatting."""

    def __init__(
        self,
        message: str = "Request validation failed",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code="NBI-1001",
            message=message,
            status_code=400,
            detail=detail,
        )


class QueryTextTooLongError(ValidationError):
    """User query text exceeds the maximum allowed length."""

    def __init__(self, length: int, max_length: int = 2_000) -> None:
        super().__init__(
            message="Query text exceeds maximum length",
            detail=f"Query length {length} exceeds maximum of {max_length} characters",
        )


class InvalidPaginationError(ValidationError):
    """Pagination parameters are out of valid range."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            message="Invalid pagination parameters",
            detail=detail,
        )


# ═══════════════════════════════════════════════════════════════════════════
# AUTHENTICATION / AUTHORIZATION EXCEPTIONS (NBI-1002, NBI-1003)
# ═══════════════════════════════════════════════════════════════════════════


class AuthenticationError(NexusBIError):
    """JWT authentication failed or token has expired."""

    def __init__(
        self,
        message: str = "Authentication failed",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code="NBI-1002",
            message=message,
            status_code=401,
            detail=detail,
        )


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""

    def __init__(self) -> None:
        super().__init__(
            message="Token has expired",
            detail="The provided access token has expired. Please refresh.",
        )


class InvalidTokenError(AuthenticationError):
    """JWT token is malformed or has an invalid signature."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid token",
            detail="The provided token is malformed or has an invalid signature.",
        )


class AuthorizationError(NexusBIError):
    """User does not have permission to access the requested resource."""

    def __init__(
        self,
        message: str = "Permission denied",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code="NBI-1003",
            message=message,
            status_code=403,
            detail=detail,
        )


class InsufficientRoleError(AuthorizationError):
    """User role does not have the required permission."""

    def __init__(self, required_role: str) -> None:
        super().__init__(
            message="Insufficient permissions",
            detail=f"This action requires the '{required_role}' role.",
        )


# ═══════════════════════════════════════════════════════════════════════════
# AI PLATFORM EXCEPTIONS (NBI-2001, NBI-2002)
# ═══════════════════════════════════════════════════════════════════════════


class AIProviderError(NexusBIError):
    """Primary and fallback LLM services failed to respond."""

    def __init__(
        self,
        message: str = "AI provider unavailable",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code="NBI-2001",
            message=message,
            status_code=504,
            detail=detail,
        )


class AITimeoutError(AIProviderError):
    """LLM provider timed out before returning a response."""

    def __init__(self, provider: str, timeout_seconds: int) -> None:
        super().__init__(
            message=f"AI provider '{provider}' timed out",
            detail=f"Request to {provider} exceeded {timeout_seconds}s timeout.",
        )


class SQLValidationError(NexusBIError):
    """Generated SQL failed AST security validation checks."""

    def __init__(
        self,
        message: str = "SQL validation failed",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code="NBI-2002",
            message=message,
            status_code=422,
            detail=detail,
        )


class UnsafeSQLError(SQLValidationError):
    """Generated SQL contains unsafe operations (DROP, DELETE, etc.)."""

    def __init__(self, statement_type: str) -> None:
        super().__init__(
            message="Unsafe SQL statement detected",
            detail=(
                f"Statement type '{statement_type}' is not allowed. "
                "Only SELECT is permitted."
            ),
        )


class PromptInjectionError(NexusBIError):
    """Input contains suspected prompt injection content."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            code="NBI-2003",
            message="Input rejected by safety filter",
            status_code=400,
            detail=detail or "The input was flagged by the security filter.",
        )


# ═══════════════════════════════════════════════════════════════════════════
# WAREHOUSE / INFRASTRUCTURE EXCEPTIONS (NBI-3001, NBI-3002)
# ═══════════════════════════════════════════════════════════════════════════


class WarehouseQueryError(NexusBIError):
    """Snowflake execution failed due to SQL syntax or database errors."""

    def __init__(
        self,
        message: str = "Data warehouse query failed",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code="NBI-3001",
            message=message,
            status_code=500,
            detail=detail,
        )


class WarehouseTimeoutError(NexusBIError):
    """Snowflake query timed out before execution completed."""

    def __init__(
        self,
        message: str = "Data warehouse query timed out",
        detail: str | None = None,
    ) -> None:
        super().__init__(
            code="NBI-3002",
            message=message,
            status_code=504,
            detail=detail,
        )


class WarehouseConnectionError(NexusBIError):
    """Could not establish a connection to the data warehouse."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            code="NBI-3003",
            message="Data warehouse connection failed",
            status_code=503,
            detail=detail or "Unable to connect to the data warehouse.",
        )


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN EXCEPTIONS (NBI-4xxx)
# ═══════════════════════════════════════════════════════════════════════════


class EntityNotFoundError(NexusBIError):
    """Requested entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            code="NBI-4001",
            message=f"{entity_type} not found",
            status_code=404,
            detail=f"{entity_type} with id '{entity_id}' does not exist.",
        )


class DuplicateEntityError(NexusBIError):
    """Entity already exists (uniqueness constraint violation)."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(
            code="NBI-4002",
            message=f"{entity_type} already exists",
            status_code=409,
            detail=f"{entity_type} with identifier '{identifier}' already exists.",
        )


class BusinessRuleViolationError(NexusBIError):
    """A domain business rule was violated."""

    def __init__(self, rule: str, detail: str | None = None) -> None:
        super().__init__(
            code="NBI-4003",
            message=f"Business rule violation: {rule}",
            status_code=422,
            detail=detail,
        )


# ═══════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE EXCEPTIONS (NBI-5xxx)
# ═══════════════════════════════════════════════════════════════════════════


class DatabaseError(NexusBIError):
    """Internal PostgreSQL metadata database error."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            code="NBI-5001",
            message="Database operation failed",
            status_code=500,
            detail=detail or "An internal database error occurred.",
        )


class CacheError(NexusBIError):
    """Redis cache operation failure."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            code="NBI-5002",
            message="Cache operation failed",
            status_code=500,
            detail=detail or "An internal cache error occurred.",
        )


class ExternalServiceError(NexusBIError):
    """An external service dependency failed."""

    def __init__(self, service: str, detail: str | None = None) -> None:
        super().__init__(
            code="NBI-5003",
            message=f"External service '{service}' is unavailable",
            status_code=503,
            detail=detail,
        )


class RateLimitExceededError(NexusBIError):
    """Client has exceeded the allowed request rate."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            code="NBI-5004",
            message="Rate limit exceeded",
            status_code=429,
            detail=detail or "Too many requests. Please try again later.",
        )


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL EXCEPTION HANDLER REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application.

    Handlers are registered in specificity order so that the most
    specific exception types are matched first.
    """

    @app.exception_handler(NexusBIError)
    async def nexusbi_error_handler(
        request: Request, exc: NexusBIError
    ) -> JSONResponse:
        """Handle all NexusBI application exceptions."""
        logger.error(
            "Application error",
            error_code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )
        return _build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic request validation errors."""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", "Validation error"),
                    "type": error.get("type", "value_error"),
                }
            )

        logger.warning(
            "Request validation failed",
            path=request.url.path,
            method=request.method,
            error_count=len(errors),
        )
        return _build_error_response(
            status_code=422,
            code="NBI-1001",
            message="Request validation failed",
            detail="One or more request fields failed validation.",
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle standard Starlette HTTP exceptions (404, 405, etc.)."""
        status_code = exc.status_code
        code_map = {
            400: "NBI-1001",
            401: "NBI-1002",
            403: "NBI-1003",
            404: "NBI-4001",
            405: "NBI-1001",
            429: "NBI-5004",
        }
        error_code = code_map.get(status_code, "NBI-9999")

        logger.warning(
            "HTTP error",
            status_code=status_code,
            detail=str(exc.detail),
            path=request.url.path,
            method=request.method,
        )
        return _build_error_response(
            status_code=status_code,
            code=error_code,
            message=str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler for unexpected server exceptions.

        In production, the detail field is sanitised to prevent
        leaking internal stack traces to the client.
        """
        logger.exception(
            "Unhandled server exception",
            path=request.url.path,
            method=request.method,
            exception_type=type(exc).__name__,
        )

        from app.core.config import settings

        if settings.is_development:
            detail = str(exc)
        else:
            detail = "An unexpected error occurred."

        return _build_error_response(
            status_code=500,
            code="NBI-9999",
            message="An unexpected server error occurred",
            detail=detail,
        )
