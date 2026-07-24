"""User Management REST API endpoints (v1 namespace).

Provides HTTP handlers for retrieving the current user profile, reading
user details by ID, and updating existing user accounts.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import (
    get_current_user,
    get_get_user_use_case,
    get_update_user_use_case,
)
from app.api.dependencies.authorization import require_permission
from app.application.dto.auth_dto import UserDTO
from app.application.dto.user_dto import UpdateUserDTO
from app.application.use_cases import GetUserUseCase, UpdateUserUseCase
from app.domain.entities.user import User

router = APIRouter(prefix="/users", tags=["User Management"])


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
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        roles=current_user.role_names,
        permissions=current_user.permission_names,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.get(
    "/{user_id}",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    summary="Get user details by ID",
    dependencies=[Depends(require_permission("users:read"))],
)
def get_user_by_id(
    user_id: str,
    use_case: Annotated[GetUserUseCase, Depends(get_get_user_use_case)],
) -> UserDTO:
    """Retrieve details for a specific user by identifier."""
    return use_case.execute(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    summary="Update user details",
    dependencies=[Depends(require_permission("users:update"))],
)
def update_user(
    user_id: str,
    dto: UpdateUserDTO,
    use_case: Annotated[UpdateUserUseCase, Depends(get_update_user_use_case)],
) -> UserDTO:
    """Update editable profile fields for a specific user."""
    return use_case.execute(user_id, dto)
