"""Infrastructure database package.

Exposes the SQLAlchemy 2.0 declarative base and all ORM models.
"""

from app.infrastructure.database.base import Base

__all__ = ["Base"]
