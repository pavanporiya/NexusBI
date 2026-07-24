"""Authentication REST API endpoints (v1 namespace).

Provides HTTP handlers for user registration, credential login, token refresh,
logout session revocation, and current user profile retrieval.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies.auth import (
    get_current_user,
    get_login_user_use_case,
    get_logout_user_use_case,
    get_refresh_token_use_case,
    get_register_user_use_case,
)
from app.application.dto.auth_dto import (
    LoginDTO,
    RegisterDTO,
    TokenDTO,
    TokenRefreshDTO,
    UserDTO,
)
from app.application.use_cases import (
    LoginUserUseCase,
    LogoutUserUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
)
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(
    dto: RegisterDTO,
    use_case: Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)],
) -> UserDTO:
    """Register a new user with email and password."""
    return use_case.execute(dto)


@router.post(
    "/login",
    response_model=TokenDTO,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue tokens",
)
def login_user(
    dto: LoginDTO,
    request: Request,
    use_case: Annotated[LoginUserUseCase, Depends(get_login_user_use_case)],
) -> TokenDTO:
    """Authenticate user credentials and return access and refresh tokens."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return use_case.execute(dto, client_ip=client_ip, user_agent=user_agent)


@router.post(
    "/refresh",
    response_model=TokenDTO,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new token pair",
)
def refresh_token(
    dto: TokenRefreshDTO,
    request: Request,
    use_case: Annotated[RefreshTokenUseCase, Depends(get_refresh_token_use_case)],
) -> TokenDTO:
    """Rotate access and refresh tokens using a valid refresh token."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return use_case.execute(dto, client_ip=client_ip, user_agent=user_agent)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke user session",
)
def logout_user(
    dto: TokenRefreshDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[LogoutUserUseCase, Depends(get_logout_user_use_case)],
) -> dict[str, str]:
    """Revoke active session for authenticated user."""
    _ = current_user
    use_case.execute(dto.refresh_token)
    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserDTO:
    """Retrieve details for the currently authenticated user."""
    return UserDTO(
        id=current_user.id,
        email=str(current_user.email),
        is_active=current_user.is_active,
        roles=current_user.role_names,
        permissions=current_user.permission_names,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
