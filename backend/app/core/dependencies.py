from typing import Generator
from dependency_injector import containers, providers
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import structlog
from app.core.config import settings

logger = structlog.get_logger()

# SQLAlchemy Base Definition
Base = declarative_base()

# Configure PostgreSQL Engine (OLTP / Metadata)
engine = create_engine(
    settings.postgres_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """FastAPI Dependency to retrieve local transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Container(containers.DeclarativeContainer):
    """Dependency injection container for all service adapters."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.health",
        ]
    )

    # Core Configurations
    config = providers.Configuration()

    # PostgreSQL Session Provider
    db_session = providers.Resource(get_db)
