"""NexusBI Infrastructure Layer (Adapters).

Contains concrete implementations of domain port interfaces,
connecting to external systems: PostgreSQL, Snowflake, Redis,
LLM APIs, and the pgvector search index.

Architecture Reference:
- phase2_1_repository_blueprint.md Section 2.3
- ADR-005: Clean Architecture
- ADR-011: Repository Pattern
"""

from app.infrastructure.database.base import Base
from app.infrastructure.mappers.session_mapper import SessionMapper
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.repositories.session_repository import (
    SQLAlchemySessionRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.services.jwt_token_service import JWTTokenService

__all__ = [
    "Base",
    "BcryptPasswordHasher",
    "JWTTokenService",
    "SQLAlchemySessionRepository",
    "SQLAlchemyUserRepository",
    "SessionMapper",
    "UserMapper",
]
