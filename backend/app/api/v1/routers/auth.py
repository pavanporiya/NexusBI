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
    LogoutResponseDTO,
    RegisterDTO,
    TokenDTO,
    TokenRefreshDTO,
    UserDTO,
)
from app.application.dto.error_dto import create_error_responses
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
    operation_id="auth_register_user",
    response_description="Newly created user account profile.",
    responses=create_error_responses(400, 409, 422, 500),
    description=(
        "Registers a new user with email and password credentials. "
        "Validates password complexity, checks for duplicate email registration, "
        "and assigns the default Viewer role."
    ),
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
    operation_id="auth_login_user",
    response_description="Access token and refresh token payload.",
    responses=create_error_responses(400, 401, 422, 500),
    description=(
        "Authenticates user email and password credentials, records client IP "
        "and User-Agent in session tracking, and returns a signed JWT access token "
        "and an opaque refresh token."
    ),
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
    operation_id="auth_refresh_token",
    response_description="Rotated access token and new refresh token pair.",
    responses=create_error_responses(400, 401, 422, 500),
    description=(
        "Validates an active opaque refresh token, revokes the preceding session, "
        "and issues a fresh JWT access token and new refresh token pair."
    ),
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
    response_model=LogoutResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Revoke user session",
    operation_id="auth_logout_user",
    response_description="Session revocation status confirmation message.",
    responses=create_error_responses(400, 401, 422, 500),
    description=(
        "Revokes the active user session associated with the supplied refresh token. "
        "Requires a valid JWT Bearer authentication token in the Authorization header."
    ),
)
def logout_user(
    dto: TokenRefreshDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[LogoutUserUseCase, Depends(get_logout_user_use_case)],
) -> LogoutResponseDTO:
    """Revoke active session for authenticated user."""
    _ = current_user
    use_case.execute(dto.refresh_token)
    return LogoutResponseDTO(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    operation_id="auth_get_me",
    response_description="Profile details, roles, and permissions of the active user.",
    responses=create_error_responses(401, 500),
    description=(
        "Retrieves detailed profile information for the currently authenticated user, "
        "including list of assigned roles and resolved permission action strings. "
        "Requires a valid JWT Bearer authentication token."
    ),
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
