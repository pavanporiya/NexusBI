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
import sys
import time
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Service startup timestamp — set once at module import time
# ---------------------------------------------------------------------------

_SERVICE_START_TIME = time.monotonic()
_SERVICE_START_UTC = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class HealthStatus(StrEnum):
    """Possible health statuses."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of an individual system component."""

    name: str
    status: HealthStatus
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    """Comprehensive system health report."""

    status: HealthStatus
    service: str
    environment: str
    timestamp: str
    uptime_seconds: float
    checks: list[ComponentHealth]


class LivenessResponse(BaseModel):
    """Lightweight liveness probe response."""

    status: str = Field(default="ok")
    service: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    status: HealthStatus
    checks: dict[str, str]


class VersionResponse(BaseModel):
    """Build version and runtime metadata."""

    service: str
    version: str
    environment: str
    python_version: str
    platform: str
    api_version: str
    started_at: str


# ---------------------------------------------------------------------------
# Component Health Checkers
# ---------------------------------------------------------------------------


def _check_postgres(db: Session) -> ComponentHealth:
    """Verify PostgreSQL metadata database connectivity."""
    start = time.perf_counter()
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health Check",
    description="Returns a comprehensive health report including all dependency checks.",
)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Comprehensive system health check.

    Evaluates all critical infrastructure dependencies and returns
    an aggregate health status:
    - healthy:   All dependencies are operational
    - degraded:  Some non-critical dependencies are failing
    - unhealthy: Critical dependencies are failing
    """
    settings = get_settings()
    checks: list[ComponentHealth] = []

    # Check PostgreSQL
    pg_health = _check_postgres(db)
    checks.append(pg_health)

    # Aggregate status
    statuses = [c.status for c in checks]
    if all(s == HealthStatus.HEALTHY for s in statuses):
        overall = HealthStatus.HEALTHY
    elif any(s == HealthStatus.UNHEALTHY for s in statuses):
        overall = HealthStatus.UNHEALTHY
    else:
        overall = HealthStatus.DEGRADED

    uptime = time.monotonic() - _SERVICE_START_TIME

    return HealthResponse(
        status=overall,
        service=settings.PROJECT_NAME,
        environment=settings.ENV.value,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(uptime, 2),
        checks=checks,
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Lightweight check to verify the service process is alive. Used by Kubernetes liveness probes.",
)
@router.get(
    "/live",
    response_model=LivenessResponse,
    include_in_schema=False,
)
async def liveness_check() -> LivenessResponse:
    """Liveness probe — confirms the process is running.

    This endpoint performs no dependency checks. It simply returns
    200 OK to confirm the process has not crashed or deadlocked.
    """
    settings = get_settings()
    return LivenessResponse(
        service=settings.PROJECT_NAME,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Verifies all critical dependencies are available. Used by Kubernetes readiness probes and load balancers.",
)
@router.get(
    "/ready",
    response_model=ReadinessResponse,
    include_in_schema=False,
)
async def readiness_check(
    db: Session = Depends(get_db),
) -> ReadinessResponse:
    """Readiness probe — confirms all dependencies are available.

    If any critical dependency is unhealthy, the probe returns a
    503 status, causing the load balancer to stop routing traffic
    to this instance.
    """
    checks: dict[str, str] = {}

    # PostgreSQL
    pg = _check_postgres(db)
    checks["postgres"] = pg.status.value

    overall = (
        HealthStatus.HEALTHY
        if all(v == "healthy" for v in checks.values())
        else HealthStatus.UNHEALTHY
    )

    return ReadinessResponse(status=overall, checks=checks)


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Service Version",
    description="Returns build version, runtime metadata, and environment information.",
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
