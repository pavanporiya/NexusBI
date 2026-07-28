"""Infrastructure connectors module.

Provides production-ready database connector implementations based on the
universal connector framework defined in the domain layer.

Current implementations:
- PostgresConnector: SQLAlchemy-based PostgreSQL connector

Usage:
    from app.infrastructure.connectors import ConnectorRegistry, PostgresConnector
    from app.domain.connectors import ConnectorConfig, ConnectorType

    config = ConnectorConfig(
        id="postgres_prod",
        name="Production Database",
        connector_type=ConnectorType.POSTGRESQL,
        host="db.example.com",
        port=5432,
        database="nexusbi",
        username="user",
        password="password"
    )

    connector = ConnectorRegistry.create(config)
    connector.connect()
    try:
        rows = connector.execute("SELECT * FROM users")
    finally:
        connector.disconnect()
"""

from __future__ import annotations

from app.infrastructure.connectors.postgres import PostgresConnector
from app.infrastructure.connectors.registry import ConnectorRegistry

__all__ = [
    "ConnectorRegistry",
    "PostgresConnector",
]
