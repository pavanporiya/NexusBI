"""NexusBI Backend Service — Application Bootstrap.

This is the entry point for the FastAPI application. It orchestrates:
1. Configuration loading from environment
2. Structured logging initialisation
3. Dependency injection container wiring
4. Middleware stack registration
5. Exception handler binding
6. API router mounting
7. Custom OpenAPI schema configuration

Architecture Reference:
- phase2_1_repository_blueprint.md Section 2.1 (API Layer)
- ADR-001: FastAPI as web framework
- ADR-005: Clean Architecture boundaries
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import get_settings
from app.core.dependencies import Container
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import setup_middleware

# ---------------------------------------------------------------------------
# OpenAPI Metadata & Documentation System
# ---------------------------------------------------------------------------

API_DESCRIPTION = (
    "### NexusBI — Enterprise Analytics Copilot API\n\n"
    "NexusBI is a production-grade, AI-powered Business Intelligence platform "
    "providing natural language to SQL translation, automated dataset insights, "
    "and enterprise role-based access control (RBAC).\n\n"
    "#### Key Features & Architecture\n"
    "- **Clean Architecture**: Domain-driven layering separating core entities, "
    "application use cases, infrastructure adapters, and API endpoints.\n"
    "- **Authentication**: JWT Bearer token authentication with session rotation "
    "and security logging.\n"
    "- **Granular RBAC**: Fine-grained permission model (`users:read`, `users:update`, "
    "`roles:read`, `roles:create`, `roles:update`, `roles:delete`).\n"
    "- **Structured Observability**: Structured JSON logging with trace "
    "correlation IDs on every request and exception.\n"
    "- **Standardized Error Taxonomy**: Consistent `NBI-XXXX` error envelopes "
    "across all HTTP status codes.\n\n"
    "#### Security & Authentication\n"
    "- Send requests to protected endpoints with an `Authorization: Bearer <token>` "
    "header.\n"
    "- Authenticate via `POST /api/v1/auth/login` to obtain access and refresh tokens."
)

OPENAPI_TAGS: list[dict[str, Any]] = [
    {
        "name": "System Health",
        "description": (
            "Liveness, readiness, and system health status monitoring endpoints "
            "for container orchestration."
        ),
    },
    {
        "name": "Authentication",
        "description": (
            "User registration, credential login, token rotation, session revocation, "
            "and current user identity."
        ),
    },
    {
        "name": "User Management",
        "description": (
            "User profile retrieval and administrative profile update operations."
        ),
    },
    {
        "name": "Role Management",
        "description": (
            "RBAC role definitions and permission assignment management endpoints."
        ),
    },
    {
        "name": "Dashboard Management",
        "description": (
            "BI dashboard creation, retrieval, updating, deleting, "
            "and paginated listing."
        ),
    },
    {
        "name": "Report Management",
        "description": (
            "Analytical report CRUD operations, query management, "
            "and paginated listing."
        ),
    },
    {
        "name": "Dataset Management",
        "description": (
            "Dataset definition, table/query metadata management, "
            "and paginated listing."
        ),
    },
    {
        "name": "Organization Management",
        "description": ("Enterprise organization CRUD operations and management."),
    },
    {
        "name": "Workspace Management",
        "description": (
            "Multi-tenant workspace CRUD operations and membership management."
        ),
    },
    {
        "name": "Widget Management",
        "description": (
            "Dashboard widget visualization CRUD operations, grid position moving, "
            "resizing, and visibility toggling."
        ),
    },
    {
        "name": "Universal Query Engine",
        "description": (
            "Single query execution layer supporting read-only SELECT validation, "
            "safe parameter binding, pagination, timeouts, and dataset previews."
        ),
    },
    {
        "name": "Universal Chart Engine",
        "description": (
            "Chart model generation, preview, and validation endpoints backed "
            "by typed chart strategies."
        ),
    },
]


def setup_openapi_schema(app: FastAPI) -> None:
    """Configure custom OpenAPI schema generator with security schemes and metadata."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
        )

        components = openapi_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["HTTPBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT Access Token authentication. Provide your token as "
                "'Bearer <JWT>' in the Authorization header. Obtain tokens via "
                "POST /api/v1/auth/login."
            ),
        }

        public_paths = {
            f"{app.state.api_prefix}/health",
            f"{app.state.api_prefix}/health/live",
            f"{app.state.api_prefix}/health/ready",
            f"{app.state.api_prefix}/version",
            f"{app.state.api_prefix}/auth/register",
            f"{app.state.api_prefix}/auth/login",
            f"{app.state.api_prefix}/auth/refresh",
        }

        for path, methods in openapi_schema.get("paths", {}).items():
            for method, operation in methods.items():
                if method.lower() in (
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "options",
                    "head",
                ):
                    if path in public_paths:
                        operation["security"] = []
                    else:
                        operation.setdefault("security", [{"HTTPBearer": []}])

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage the application startup and shutdown lifecycle."""
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
    """Construct and configure the FastAPI application instance."""
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
        title="NexusBI Backend API",
        description=API_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=(f"{settings.API_V1_STR}/docs" if settings.is_development else None),
        redoc_url=(f"{settings.API_V1_STR}/redoc" if settings.is_development else None),
        openapi_tags=OPENAPI_TAGS,
        servers=[
            {
                "url": f"http://{settings.HOST}:{settings.PORT}",
                "description": f"{settings.ENV.value.capitalize()} Server",
            }
        ],
        contact={
            "name": "NexusBI Platform Team",
            "email": "engineering@nexusbi.io",
            "url": "https://nexusbi.io",
        },
        license_info={
            "name": "Proprietary",
            "url": "https://nexusbi.io/license",
        },
        lifespan=lifespan,
    )

    # Attach container and metadata to application state
    app.state.container = container
    app.state.api_prefix = settings.API_V1_STR

    # 5. Register middleware stack
    setup_middleware(app)
    logger.info("Middleware stack registered")

    # 6. Register exception handlers
    register_exception_handlers(app)
    logger.info("Exception handlers registered")

    # 7. Mount API routers
    _register_routers(app, settings.API_V1_STR)
    logger.info("API routers mounted", api_prefix=settings.API_V1_STR)

    # 8. Setup custom OpenAPI schema generator
    setup_openapi_schema(app)
    logger.info("OpenAPI schema configuration complete")

    return app


def _register_routers(app: FastAPI, api_prefix: str) -> None:
    """Mount all API routers under the versioned prefix."""
    from app.api.health import router as health_router
    from app.api.v1.routers.auth import router as auth_router
    from app.api.v1.routers.charts import router as charts_router
    from app.api.v1.routers.dashboards import router as dashboards_router
    from app.api.v1.routers.datasets import router as datasets_router
    from app.api.v1.routers.organizations import router as organizations_router
    from app.api.v1.routers.query import router as query_router
    from app.api.v1.routers.reports import router as reports_router
    from app.api.v1.routers.roles import router as roles_router
    from app.api.v1.routers.users import router as users_router
    from app.api.v1.routers.widgets import router as widgets_router
    from app.api.v1.routers.workspaces import router as workspaces_router

    # Health endpoints are mounted under the API prefix
    app.include_router(
        health_router,
        prefix=api_prefix,
        tags=["System Health"],
    )

    # Also mount core health endpoints at root for Kubernetes probes
    app.include_router(
        health_router,
        tags=["System Health (Root)"],
        include_in_schema=False,
    )

    # Mount Authentication REST API endpoints
    app.include_router(
        auth_router,
        prefix=api_prefix,
    )

    # Mount User Management REST API endpoints
    app.include_router(
        users_router,
        prefix=api_prefix,
    )

    # Mount Role Management REST API endpoints
    app.include_router(
        roles_router,
        prefix=api_prefix,
    )

    # Mount Dashboard Management REST API endpoints
    app.include_router(
        dashboards_router,
        prefix=api_prefix,
    )

    # Mount Widget Management REST API endpoints
    app.include_router(
        widgets_router,
        prefix=api_prefix,
    )

    # Mount Report Management REST API endpoints
    app.include_router(
        reports_router,
        prefix=api_prefix,
    )

    # Mount Dataset Management REST API endpoints
    app.include_router(
        datasets_router,
        prefix=api_prefix,
    )

    # Mount Organization Management REST API endpoints
    app.include_router(
        organizations_router,
        prefix=api_prefix,
    )

    # Mount Workspace Management REST API endpoints
    app.include_router(
        workspaces_router,
        prefix=api_prefix,
    )

    # Mount Universal Query Engine REST API endpoints
    app.include_router(
        query_router,
        prefix=api_prefix,
    )

    # Mount Universal Chart Engine REST API endpoints
    app.include_router(
        charts_router,
        prefix=api_prefix,
    )


# ---------------------------------------------------------------------------
# Module-level application instance
# ---------------------------------------------------------------------------

app = create_app()
