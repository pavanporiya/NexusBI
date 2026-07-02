"""NexusBI Dependency Injection Container.

Implements the Dependency Injector pattern using the dependency-injector
library, organizing services according to Clean Architecture boundaries:

- Core Layer: Configuration, logging, database engines
- Infrastructure Layer: Adapter clients (Snowflake, Redis, LLM, pgvector)
- Domain Layer: Use case orchestrators

Architecture Reference:
- phase2_1_repository_blueprint.md Section 3 (Dependency Rules)
- ADR-005: Clean Architecture
- ADR-011: Repository Pattern
"""

from __future__ import annotations

from collections.abc import Generator

from dependency_injector import containers, providers
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import Settings, get_settings
from app.core.logging import AuditLogger, get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# SQLAlchemy Base Definition
# ---------------------------------------------------------------------------

Base = declarative_base()

# ---------------------------------------------------------------------------
# Database Session Factory
# ---------------------------------------------------------------------------


def _create_engine(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine from application settings."""
    return create_engine(
        settings.postgres_dsn,
        pool_pre_ping=True,
        pool_size=settings.POSTGRES_POOL_SIZE,
        max_overflow=settings.POSTGRES_MAX_OVERFLOW,
        pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
        echo=settings.POSTGRES_ECHO,
        pool_recycle=3600,
    )


def _create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory bound to the engine."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )


def get_db() -> Generator[Session]:
    """FastAPI dependency that yields a scoped database session.

    The session is automatically closed after the request completes,
    regardless of success or failure.
    """
    settings = get_settings()
    engine = _create_engine(settings)
    session_factory = _create_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Dependency Injection Container
# ---------------------------------------------------------------------------


class Container(containers.DeclarativeContainer):
    """Root dependency injection container for the NexusBI backend.

    Organised in Clean Architecture layers:

    Core
    ├── config          → Application settings singleton
    ├── logging         → Structured logger factory
    └── audit_logger    → Compliance audit logger

    Infrastructure
    ├── db_engine       → SQLAlchemy engine
    ├── db_session_factory → Session maker
    └── db_session      → Scoped session provider

    Wiring binds this container's providers to the API layer modules
    so FastAPI's ``Depends()`` can resolve them at request time.
    """

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.health",
            "app.api.v1.routers.health",
        ],
    )

    # ── Core Layer ─────────────────────────────────────────────────────

    config = providers.Singleton(get_settings)

    audit_logger = providers.Singleton(AuditLogger)

    # ── Infrastructure Layer: Database ─────────────────────────────────

    db_engine = providers.Singleton(
        _create_engine,
        settings=config,
    )

    db_session_factory = providers.Singleton(
        _create_session_factory,
        engine=db_engine,
    )

    db_session = providers.Resource(
        get_db,
    )
