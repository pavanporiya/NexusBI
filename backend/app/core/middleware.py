"""NexusBI Middleware Stack.

Provides production-grade middleware for request tracing, structured
logging, CORS policy, response compression, security headers, and
request timing.

Architecture Reference:
- phase2_1_repository_blueprint.md Section 3.1 (Core Layer)
- phase2_3_api_service_blueprint.md Section 7 (Observability)
"""

from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import (
    get_logger,
    reset_correlation_id,
    set_correlation_id,
)

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST ID MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a unique request/trace ID to every incoming request.

    The ID is sourced from the ``X-Request-ID`` or ``X-Trace-ID``
    header if present, otherwise a new UUID is generated. The ID is
    propagated via:
    1. The ``correlation_id`` context variable (for structured logs)
    2. The ``X-Request-ID`` response header (for client correlation)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = (
            request.headers.get("x-request-id")
            or request.headers.get("x-trace-id")
            or uuid.uuid4().hex
        )

        # Bind the correlation ID into the async context
        set_correlation_id(request_id)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            trace_id=request_id,
        )

        # Store on request state for downstream access
        request.state.request_id = request_id

        response = await call_next(request)

        # Propagate request ID to the client
        response.headers["X-Request-ID"] = request_id

        # Cleanup context
        reset_correlation_id()

        return response


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST LOGGING MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, and duration.

    Skips logging for health check endpoints to reduce noise.
    """

    SKIP_PATHS: frozenset[str] = frozenset({
        "/health",
        "/live",
        "/ready",
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
    })

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # Skip health check noise
        if path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()

        logger.info(
            "Request started",
            method=request.method,
            path=path,
            query_params=str(request.query_params) if request.query_params else None,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            log_method = logger.info if response.status_code < 400 else logger.warning
            log_method(
                "Request completed",
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Inject timing header
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed with exception",
                method=request.method,
                path=path,
                duration_ms=round(duration_ms, 2),
                exception_type=type(exc).__name__,
                error=str(exc),
            )
            raise

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract the real client IP from proxy headers or connection."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# SECURITY HEADERS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        if not settings.is_development:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST TIMING MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════


class TimingMiddleware(BaseHTTPMiddleware):
    """Add a ``Server-Timing`` header for performance observability.

    This conforms to the W3C Server-Timing specification, enabling
    browser DevTools and monitoring tools to display server-side
    processing time.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["Server-Timing"] = f"total;dur={duration_ms:.2f}"

        return response


# ═══════════════════════════════════════════════════════════════════════════
# MIDDLEWARE REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI application.

    Middleware is added in reverse execution order — the last
    middleware added is the first to process the request.

    Execution order (request flow):
    1. RequestIDMiddleware      → Assigns correlation ID
    2. RequestLoggingMiddleware → Logs request lifecycle
    3. TimingMiddleware         → Measures processing time
    4. SecurityHeadersMiddleware → Injects security headers
    5. GZipMiddleware           → Compresses response body
    6. CORSMiddleware           → Applies CORS policy
    """
    # 6. CORS (outermost in the response chain)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-Trace-ID",
            "Accept",
        ],
        expose_headers=["X-Request-ID", "X-Response-Time", "Server-Timing"],
    )

    # 5. Response compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 4. Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Server timing
    app.add_middleware(TimingMiddleware)

    # 2. Request logging (skips health checks)
    if settings.ENABLE_REQUEST_LOGGING:
        app.add_middleware(RequestLoggingMiddleware)

    # 1. Request ID assignment (innermost = first to run)
    app.add_middleware(RequestIDMiddleware)
