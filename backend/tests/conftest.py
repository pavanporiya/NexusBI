"""NexusBI Test Configuration and Fixtures.

Provides shared pytest fixtures for the backend test suite:
- Test application instance
- HTTP test client
- Database session mocking
- Settings overrides for testing environment
"""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings


@pytest.fixture(scope="session")
def test_settings() -> Generator[Settings]:
    """Provide test-specific settings overrides."""
    import os

    os.environ["ENV"] = "testing"
    os.environ["DEBUG"] = "true"
    os.environ["PROJECT_NAME"] = "NexusBI Backend"
    os.environ["SECRET_KEY"] = "test_secret_key_not_for_production"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_DB"] = "nexusbi_testing"
    os.environ["ENABLE_REQUEST_LOGGING"] = "true"

    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    yield settings

    get_settings.cache_clear()


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Provide a mock database session for unit tests."""
    session = MagicMock()
    session.execute.return_value = MagicMock()
    return session


@pytest.fixture
def app(test_settings: Settings, mock_db_session: MagicMock) -> Generator[FastAPI]:  # noqa: ARG001
    """Create a test application instance with mocked dependencies."""
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.dependencies import get_db
    from app.main import create_app

    application = create_app()

    def override_get_db() -> Generator[MagicMock]:
        try:
            yield mock_db_session
        finally:
            mock_db_session.close()

    application.dependency_overrides[get_db] = override_get_db

    yield application

    application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient]:
    """Provide an HTTP test client bound to the test application."""
    with TestClient(app) as test_client:
        yield test_client
