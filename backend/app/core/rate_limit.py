"""Redis-based sliding window rate limiting middleware.

Provides per-IP rate limiting with configurable windows and limits.
Falls back to in-memory tracking if Redis is unavailable.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger(__name__)

# Paths exempt from rate limiting
_EXEMPT_PATHS = frozenset(
    {
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
    }
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter using Redis with in-memory fallback.

    Parameters
    ----------
    default_limit : int
        Max requests per window for general API endpoints.
    login_limit : int
        Max login attempts per window.
    agent_limit : int
        Max agent queries per window.
    window_seconds : int
        Sliding window duration in seconds.
    redis_client : Any | None
        Optional Redis client instance.
    """

    def __init__(
        self,
        app: Any,
        *,
        default_limit: int = 60,
        login_limit: int = 10,
        agent_limit: int = 10,
        window_seconds: int = 60,
        redis_client: Any | None = None,
    ) -> None:
        super().__init__(app)
        self._default_limit = default_limit
        self._login_limit = login_limit
        self._agent_limit = agent_limit
        self._window = window_seconds
        self._redis = redis_client
        # In-memory fallback
        self._memory_store: dict[str, list[float]] = defaultdict(list)
        self._memory_cleanup_at = time.monotonic() + 300

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, respecting X-Forwarded-For."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_limit_and_key(self, request: Request) -> tuple[int, str]:
        """Determine rate limit and cache key for the request."""
        path = request.url.path
        ip = self._get_client_ip(request)

        if path == "/api/v1/auth/login":
            return self._login_limit, f"rl:login:{ip}"
        if path.startswith("/api/v1/agents/query"):
            return self._agent_limit, f"rl:agent:{ip}"
        return self._default_limit, f"rl:api:{ip}"

    def _check_redis(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using Redis sliding window."""
        if self._redis is None:
            return True, limit

        try:
            now = time.time()
            window_start = now - self._window

            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self._window + 1)
            results = pipe.execute()

            count = results[2]
            remaining = max(0, limit - count)
            return count <= limit, remaining
        except Exception:
            logger.warning("Redis rate limit check failed, allowing request")
            return True, limit

    def _check_memory(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using in-memory sliding window."""
        now = time.time()
        window_start = now - self._window

        # Periodic cleanup
        if now > self._memory_cleanup_at:
            self._memory_cleanup_at = now + 300
            cutoff = now - self._window * 2
            for k in list(self._memory_store):
                self._memory_store[k] = [t for t in self._memory_store[k] if t > cutoff]
                if not self._memory_store[k]:
                    del self._memory_store[k]

        self._memory_store[key].append(now)
        self._memory_store[key] = [
            t for t in self._memory_store[key] if t > window_start
        ]

        count = len(self._memory_store[key])
        remaining = max(0, limit - count)
        return count <= limit, remaining

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        path = request.url.path

        # Exempt health checks and non-API paths
        if path in _EXEMPT_PATHS or not path.startswith("/api/"):
            resp: Response = await call_next(request)
            return resp

        limit, key = self._get_limit_and_key(request)

        # Try Redis first, fall back to memory
        if self._redis is not None:
            allowed, remaining = self._check_redis(key, limit)
        else:
            allowed, remaining = self._check_memory(key, limit)

        if not allowed:
            retry_after = self._window
            logger.warning(
                "Rate limit exceeded",
                key=key,
                limit=limit,
                path=path,
                ip=self._get_client_ip(request),
            )
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": {
                        "code": "NBI-4290",
                        "message": "Rate limit exceeded",
                        "detail": (
                            f"Too many requests. Limit: {limit} per {self._window}s."
                        ),
                        "retry_after": retry_after,
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
