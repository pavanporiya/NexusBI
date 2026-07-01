from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
import structlog
from app.api.health import router as health_router
from app.core.config import settings
from app.core.dependencies import Container
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import setup_middleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle manager for the FastAPI container."""
    logger.info("Starting up NexusBI API Service...")
    yield
    logger.info("Shutting down NexusBI API Service...")


def create_app() -> FastAPI:
    # 1. Setup Structured Logging configuration
    configure_logging()

    # 2. Setup Dependency Injection Container wiring
    container = Container()
    container.init_resources()

    # 3. Instantiate FastAPI Application
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Attach container instance to app
    app.state.container = container

    # 4. Bind Middlewares & Exception Handlers
    setup_middleware(app)
    register_exception_handlers(app)

    # 5. Bind API Route namespaces
    app.include_router(health_router, prefix=settings.API_V1_STR, tags=["System Health"])

    return app


app = create_app()
