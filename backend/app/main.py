"""NexusBI Backend Service — Application Bootstrap.

This is the entry point for the FastAPI application. It orchestrates:
1. Configuration loading from environment
2. Structured logging initialisation
3. Dependency injection container wiring
4. Middleware stack registration
5. Exception handler binding
6. API router mounting

Architecture Reference:
- phase2_1_repository_blueprint.md Section 2.1 (API Layer)
- ADR-001: FastAPI as web framework
- ADR-005: Clean Architecture boundaries
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.dependencies import Container
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import setup_middleware

# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the application startup and shutdown lifecycle.

    Startup:
    - Logs service start event with environment metadata
    - Validates critical configuration

    Shutdown:
    - Logs service stop event
    - Releases container resources
    """
    settings = get_settings()
    logger = get_logger("nexusbi.lifecycle")

    logger.info(
        "NexusBI API Service starting",
        version=settings.VERSION,
        environment=settings.ENV.value,
        debug=settings.DEBUG,
        api_prefix=settings.API_V1_STR,
        host=settings.HOST,
        port=settings.PORT,
    )

    yield

    logger.info("NexusBI API Service shutting down")

    # Cleanup DI container resources
    container: Container | None = getattr(app.state, "container", None)
    if container is not None:
        container.shutdown_resources()
        logger.info("Dependency injection container resources released")


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance.

    This factory follows a deterministic initialisation sequence:
    1. Load configuration
    2. Configure structured logging
    3. Initialise dependency injection container
    4. Create FastAPI application
    5. Register middleware stack
    6. Register exception handlers
    7. Mount API routers

    Returns
    -------
    A fully configured FastAPI application instance.
    """
    # 1. Load configuration
    settings = get_settings()

    # 2. Configure structured logging
    configure_logging(
        log_level=settings.python_log_level,
        json_output=not settings.is_development,
        environment=settings.ENV.value,
    )

    logger = get_logger("nexusbi.bootstrap")
    logger.info("Configuration loaded", environment=settings.ENV.value)

    # 3. Initialise dependency injection container
    container = Container()
    container.init_resources()
    logger.info("Dependency injection container initialised")

    # 4. Create FastAPI application
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Enterprise Analytics Copilot — AI-powered business intelligence platform",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs" if settings.is_development else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Attach container to application state
    app.state.container = container

    # 5. Register middleware stack
    setup_middleware(app)
    logger.info("Middleware stack registered")

    # 6. Register exception handlers
    register_exception_handlers(app)
    logger.info("Exception handlers registered")

    # 7. Mount API routers
    _register_routers(app, settings.API_V1_STR)
    logger.info("API routers mounted", api_prefix=settings.API_V1_STR)

    return app


def _register_routers(app: FastAPI, api_prefix: str) -> None:
    """Mount all API routers under the versioned prefix.

    Routers are registered in a deterministic order for predictable
    route resolution.
    """
    from app.api.health import router as health_router

    # Health endpoints are mounted at the root and under the API prefix
    app.include_router(
        health_router,
        prefix=api_prefix,
        tags=["System Health"],
    )

    # Also mount core health endpoints at the root for Kubernetes probes
    # that expect /health, /live, /ready at the root path
    app.include_router(
        health_router,
        tags=["System Health (Root)"],
        include_in_schema=False,
    )


# ---------------------------------------------------------------------------
# Module-level application instance
# ---------------------------------------------------------------------------

app = create_app()
