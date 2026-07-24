"""SQLAlchemy 2.0 Declarative Base.

Provides the canonical ORM base class with standardized naming conventions
for all database constraints. Every ORM model in the infrastructure layer
must inherit from this ``Base``.

Naming Convention Reference:
    https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Standardized naming conventions ensure deterministic constraint names
# across all environments. This is critical for Alembic migrations to
# produce consistent DDL regardless of the platform.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Application-wide SQLAlchemy 2.0 declarative base.

    All ORM models inherit from this class to share:
    - A unified ``MetaData`` instance with naming conventions.
    - Common configuration for Alembic auto-generation.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
