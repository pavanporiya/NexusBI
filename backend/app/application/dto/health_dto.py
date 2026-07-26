"""Health DTO definitions for NexusBI application."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(StrEnum):
    """Possible health statuses for overall system and components."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNAVAILABLE = "unavailable"


class ComponentHealth(BaseModel):
    """Health status of an individual system component or dependency."""

    name: str = Field(
        ...,
        description="Subsystem or dependency component identifier name",
        examples=["postgres"],
    )
    status: HealthStatus = Field(
        ...,
        description="Health status of the component",
        examples=[HealthStatus.HEALTHY],
    )
    latency_ms: float | None = Field(
        default=None,
        description="Ping execution latency in milliseconds",
        examples=[1.42],
    )
    detail: str | None = Field(
        default=None,
        description="Detailed diagnostic or failure message",
        examples=[None],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "postgres",
                "status": "healthy",
                "latency_ms": 1.42,
                "detail": None,
            }
        }
    )


class HealthResponse(BaseModel):
    """Comprehensive system health report DTO."""

    status: HealthStatus = Field(
        ...,
        description="Aggregate overall system health status",
        examples=[HealthStatus.HEALTHY],
    )
    version: str = Field(
        ...,
        description="Semantic application release version",
        examples=["1.0.0"],
    )
    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC check timestamp",
        examples=["2026-07-24T22:28:37Z"],
    )
    service: str = Field(
        ...,
        description="Service application name",
        examples=["NexusBI Backend"],
    )
    environment: str = Field(
        ...,
        description="Runtime environment name",
        examples=["development"],
    )
    uptime_seconds: float = Field(
        ...,
        description="Service process uptime duration in seconds",
        examples=[1234.56],
    )
    checks: list[ComponentHealth] = Field(
        ...,
        description="Detailed array of individual component health evaluations",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-07-24T22:28:37Z",
                "service": "NexusBI Backend",
                "environment": "development",
                "uptime_seconds": 1234.56,
                "checks": [
                    {
                        "name": "postgres",
                        "status": "healthy",
                        "latency_ms": 1.42,
                        "detail": None,
                    },
                    {
                        "name": "redis",
                        "status": "healthy",
                        "latency_ms": 0.85,
                        "detail": None,
                    },
                ],
            }
        }
    )


class LivenessResponse(BaseModel):
    """Lightweight liveness probe response DTO."""

    status: str = Field(
        default="ok",
        description="Process liveness status string",
        examples=["ok"],
    )
    service: str = Field(
        ...,
        description="Service identifier name",
        examples=["NexusBI Backend"],
    )
    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp when liveness probe ran",
        examples=["2026-07-24T22:28:37Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "service": "NexusBI Backend",
                "timestamp": "2026-07-24T22:28:37Z",
            }
        }
    )


class ReadinessResponse(BaseModel):
    """Readiness probe response DTO."""

    status: HealthStatus = Field(
        ...,
        description="Aggregate dependency readiness status",
        examples=[HealthStatus.HEALTHY],
    )
    checks: dict[str, str] = Field(
        ...,
        description="Dictionary mapping dependency name to readiness status string",
        examples=[{"postgres": "healthy", "redis": "healthy"}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "checks": {"postgres": "healthy", "redis": "healthy"},
            }
        }
    )


class VersionResponse(BaseModel):
    """Build version and runtime metadata response DTO."""

    service: str = Field(
        ...,
        description="Service identifier name",
        examples=["NexusBI Backend"],
    )
    version: str = Field(
        ...,
        description="Semantic application release version",
        examples=["1.0.0"],
    )
    environment: str = Field(
        ...,
        description="Active deployment environment",
        examples=["development"],
    )
    python_version: str = Field(
        ...,
        description="Python interpreter runtime version",
        examples=["3.14.0"],
    )
    platform: str = Field(
        ...,
        description="Host operating system platform",
        examples=["Linux"],
    )
    api_version: str = Field(
        ...,
        description="API major version path prefix",
        examples=["/api/v1"],
    )
    started_at: str = Field(
        ...,
        description="ISO-8601 UTC timestamp when service started",
        examples=["2026-07-24T20:00:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service": "NexusBI Backend",
                "version": "1.0.0",
                "environment": "development",
                "python_version": "3.14.0",
                "platform": "Linux",
                "api_version": "/api/v1",
                "started_at": "2026-07-24T20:00:00Z",
            }
        }
    )
