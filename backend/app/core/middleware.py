import time
import uuid
from typing import Awaitable, Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to inject trace IDs and track request durations."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Extract or generate Trace ID
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(trace_id=trace_id)

        start_time = time.perf_counter()
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            response.headers["x-trace-id"] = trace_id
            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed",
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise


def setup_middleware(app: FastAPI) -> None:
    # Set CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Set Tracing middleware
    app.add_middleware(TracingMiddleware)
