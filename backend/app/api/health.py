"""NexusBI Health Platform.

Production-grade health check endpoints returning structured responses
for container orchestration (Kubernetes liveness/readiness probes),
load balancer health checks, and operational monitoring.

Endpoints:
- GET /health       → Comprehensive system health report
- GET /health/live  → Lightweight liveness probe (is the process alive?)
- GET /health/ready → Readiness probe (are dependencies available?)
- GET /version      → Build version and runtime metadata

Architecture Reference:
- phase2_1_repository_blueprint.md Section 2.1 (API Layer)
- phase2_3_api_service_blueprint.md Section 2 (API Inventory)
"""

from __future__ import annotations

import platform
import socket
import sys
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.dto.error_dto import create_error_responses
from app.application.dto.health_dto import (
    ComponentHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
    VersionResponse,
)
from app.core.config import Settings, get_settings
from app.core.dependencies import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Service startup timestamp — set once at module import time
# ---------------------------------------------------------------------------

_SERVICE_START_TIME = time.monotonic()
_SERVICE_START_UTC = datetime.now(UTC)


# ---------------------------------------------------------------------------
# Component Health Checkers
# ---------------------------------------------------------------------------


def _check_postgres(db: Session | None) -> ComponentHealth:
    """Verify PostgreSQL metadata database connectivity."""
    start = time.perf_counter()
    if db is None:
        return ComponentHealth(
            name="postgres",
            status=HealthStatus.UNAVAILABLE,
            detail="Database session unavailable",
        )
    try:
        db.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="postgres",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.error("Health check: PostgreSQL unreachable", error=str(exc))
        return ComponentHealth(
            name="postgres",
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            detail=str(exc),
        )


def _check_redis(settings: Settings) -> ComponentHealth:
    """Verify Redis cache server connectivity."""
    start = time.perf_counter()
    if not settings.REDIS_HOST:
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNAVAILABLE,
            detail="Redis host is not configured",
        )

    try:
        import redis

        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=(
                settings.REDIS_PASSWORD.get_secret_value()
                if settings.REDIS_PASSWORD
                else None
            ),
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )
        if r.ping():
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency_ms, 2),
            )
        else:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency_ms, 2),
                detail="Redis PING returned False",
            )
    except ImportError:
        # Fallback to TCP socket probe if redis package is not installed
        try:
            with socket.create_connection(
                (settings.REDIS_HOST, settings.REDIS_PORT), timeout=1.0
            ):
                latency_ms = (time.perf_counter() - start) * 1000
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    latency_ms=round(latency_ms, 2),
                )
        except Exception as socket_exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.warning(
                "Health check: Redis socket unreachable", error=str(socket_exc)
            )
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNAVAILABLE,
                latency_ms=round(latency_ms, 2),
                detail=str(socket_exc),
            )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning("Health check: Redis unreachable", error=str(exc))
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNAVAILABLE,
            latency_ms=round(latency_ms, 2),
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health Check",
    operation_id="health_get_system_health",
    response_description="System health report and dependency statuses.",
    responses=create_error_responses(500),
    description=(
        "Returns a comprehensive health report including all dependency checks. "
        "Evaluates PostgreSQL database and Redis health, reporting overall status."
    ),
)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Comprehensive system health check.

    Evaluates all critical infrastructure dependencies and returns
    an aggregate health status:
    - healthy:   All dependencies are operational
    - degraded:  Some non-critical dependencies are unavailable
    - unhealthy: Critical dependencies are failing
    """
    settings = get_settings()
    checks: list[ComponentHealth] = []

    # Check PostgreSQL
    pg_health = _check_postgres(db)
    checks.append(pg_health)

    # Check Redis
    redis_health = _check_redis(settings)
    checks.append(redis_health)

    # Aggregate status
    statuses = [c.status for c in checks]
    if all(s == HealthStatus.HEALTHY for s in statuses):
        overall = HealthStatus.HEALTHY
    elif pg_health.status == HealthStatus.UNHEALTHY:
        overall = HealthStatus.UNHEALTHY
    else:
        overall = HealthStatus.DEGRADED

    uptime = time.monotonic() - _SERVICE_START_TIME

    return HealthResponse(
        status=overall,
        version=settings.VERSION,
        timestamp=datetime.now(UTC).isoformat(),
        service=settings.PROJECT_NAME,
        environment=settings.ENV.value,
        uptime_seconds=round(uptime, 2),
        checks=checks,
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    operation_id="health_get_liveness_probe",
    response_description="Lightweight process liveness confirmation.",
    responses=create_error_responses(500),
    description=(
        "Lightweight check to verify the service process is alive. "
        "Used by Kubernetes liveness probes to detect crashed containers."
    ),
)
@router.get(
    "/live",
    response_model=LivenessResponse,
    include_in_schema=False,
)
async def liveness_check() -> LivenessResponse:
    """Liveness probe — confirms the process is running.

    This endpoint performs no dependency checks. It simply returns
    200 OK with status='ok' to confirm the process has not crashed or deadlocked.
    """
    settings = get_settings()
    return LivenessResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    operation_id="health_get_readiness_probe",
    response_description="Dependency readiness status report.",
    responses=create_error_responses(500, 503),
    description=(
        "Verifies all critical dependencies (database, redis) are available. "
        "Used by Kubernetes readiness probes and load balancers."
    ),
)
@router.get(
    "/ready",
    response_model=ReadinessResponse,
    include_in_schema=False,
)
async def readiness_check(
    response: Response,
    db: Session = Depends(get_db),
) -> ReadinessResponse:
    """Readiness probe — confirms all dependencies are available.

    If any critical dependency is unhealthy, the probe sets a 503 status code
    and returns an aggregate status of unhealthy so load balancers stop routing traffic.
    If dependencies are unavailable, gracefully reports status without crashing.
    """
    settings = get_settings()
    checks: dict[str, str] = {}

    # PostgreSQL
    pg = _check_postgres(db)
    checks["postgres"] = pg.status.value

    # Redis
    r_health = _check_redis(settings)
    checks["redis"] = r_health.status.value

    if pg.status == HealthStatus.HEALTHY and r_health.status == HealthStatus.HEALTHY:
        overall = HealthStatus.HEALTHY
    elif pg.status == HealthStatus.HEALTHY and r_health.status in (
        HealthStatus.DEGRADED,
        HealthStatus.UNAVAILABLE,
    ):
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.UNHEALTHY

    if overall == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(status=overall, checks=checks)


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Service Version",
    operation_id="health_get_version_info",
    response_description="Build version and runtime metadata.",
    responses=create_error_responses(500),
    description=(
        "Returns build version, runtime metadata, Python environment details, "
        "and service start time."
    ),
)
async def version_info() -> VersionResponse:
    """Return build version and runtime metadata."""
    settings = get_settings()
    return VersionResponse(
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENV.value,
        python_version=sys.version.split()[0],
        platform=platform.system(),
        api_version=settings.API_V1_STR,
        started_at=_SERVICE_START_UTC.isoformat(),
    )
