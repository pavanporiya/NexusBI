"""Get user by ID use case.

Orchestrates loading a user profile by unique user identifier.
"""

from __future__ import annotations

from app.application.dto.auth_dto import UserDTO
from app.core.exceptions import BusinessRuleViolationError, EntityNotFoundError
from app.domain.repositories.user_repository import IUserRepository


class GetUserByIdUseCase:
    """Orchestrates loading a user profile by unique user ID."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repo = user_repository

    def execute(self, user_id: str) -> UserDTO:
        """Retrieve user details for the given user ID.

        Parameters
        ----------
        user_id : str
            The unique identifier of the user to retrieve.

        Returns
        -------
        UserDTO
            The user profile data transfer object.

        Raises
        ------
        EntityNotFoundError
            If no user exists with the given user_id.
        BusinessRuleViolationError
            If the user account is inactive.
        """
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)

        if not user.is_active:
            raise BusinessRuleViolationError(
                "User account is inactive",
                detail=f"User with ID '{user_id}' is inactive.",
            )

        return UserDTO(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            is_active=user.is_active,
            roles=user.role_names,
            permissions=user.permission_names,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
