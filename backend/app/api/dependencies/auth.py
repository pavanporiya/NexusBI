"""Authentication FastAPI dependencies.

Provides reusable dependency functions for resolving the current authenticated
user entity using Clean Architecture use cases and repositories.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.services.interfaces import IAuthorizationService, ITokenService
from app.application.use_cases.get_current_user import GetCurrentUserUseCase
from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.exceptions import AuthenticationError
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from app.infrastructure.services.authorization_service import AuthorizationService
from app.infrastructure.services.jwt_token_service import JWTTokenService

security = HTTPBearer(auto_error=False)


def get_token_service() -> ITokenService:
    """Dependency provider for ITokenService."""
    settings = get_settings()
    return JWTTokenService(
        secret_key=settings.SECRET_KEY.get_secret_value(),
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_user_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IUserRepository:
    """Dependency provider for IUserRepository."""
    return SQLAlchemyUserRepository(db)


def get_authorization_service() -> IAuthorizationService:
    """Dependency provider for IAuthorizationService."""
    return AuthorizationService()


def get_current_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> GetCurrentUserUseCase:
    """Dependency provider for GetCurrentUserUseCase."""
    return GetCurrentUserUseCase(
        user_repository=user_repo,
        token_service=token_service,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    use_case: Annotated[GetCurrentUserUseCase, Depends(get_current_user_use_case)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> User:
    """FastAPI dependency that resolves the authenticated User domain entity.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials | None
        Bearer token credentials extracted from the Authorization header.
    use_case : GetCurrentUserUseCase
        Use case orchestrator for token decoding and verification.
    user_repo : IUserRepository
        Repository interface used to load the rich User domain entity.

    Returns
    -------
    User
        The authenticated active User domain entity.

    Raises
    ------
    AuthenticationError
        If authorization credentials are missing or the token/user is invalid.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError(
            "Not authenticated", detail="Missing authorization header"
        )

    token = credentials.credentials
    user_dto = use_case.execute(token)

    user = user_repo.get_by_id(user_dto.id)
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return user
