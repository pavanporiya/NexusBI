"""Update user profile use case.

Orchestrates updating user profile details with business rule validation.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.dto.auth_dto import UserDTO
from app.application.dto.user_dto import UpdateUserProfileDTO
from app.core.exceptions import (
    BusinessRuleViolationError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from app.domain.repositories.user_repository import IUserRepository
from app.domain.value_objects.email import Email


class UpdateUserProfileUseCase:
    """Orchestrates user profile updates and validates business rules."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repo = user_repository

    def execute(self, user_id: str, dto: UpdateUserProfileDTO) -> UserDTO:
        """Update user fields for the specified user ID.

        Parameters
        ----------
        user_id : str
            The unique identifier of the user to update.
        dto : UpdateUserProfileDTO
            Data containing optional update fields.

        Returns
        -------
        UserDTO
            The updated user profile data.

        Raises
        ------
        EntityNotFoundError
            If no user exists with the given user_id.
        BusinessRuleViolationError
            If the user is inactive, an invalid update is attempted,
            or an attempt is made to modify an immutable field.
        DuplicateEntityError
            If email is being updated to an email address already in use.
        """
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)

        if not user.is_active:
            raise BusinessRuleViolationError(
                "User account is inactive",
                detail=f"User with ID '{user_id}' is inactive and cannot be updated.",
            )

        # Validate immutable fields cannot be modified
        if dto.id is not None and dto.id != user.id:
            raise BusinessRuleViolationError(
                "Immutable field modification",
                detail="Cannot modify immutable field 'id'.",
            )
        if dto.created_at is not None and dto.created_at != user.created_at:
            raise BusinessRuleViolationError(
                "Immutable field modification",
                detail="Cannot modify immutable field 'created_at'.",
            )
        if dto.google_id is not None and dto.google_id != user.google_id:
            raise BusinessRuleViolationError(
                "Immutable field modification",
                detail="Cannot modify immutable field 'google_id'.",
            )

        updated = False

        if dto.full_name is not None:
            cleaned_name = dto.full_name.strip()
            if not cleaned_name:
                raise BusinessRuleViolationError(
                    "Invalid user profile update",
                    detail="Full name cannot be empty.",
                )
            if cleaned_name != user.full_name:
                user.full_name = cleaned_name
                updated = True

        if dto.email is not None and str(dto.email) != str(user.email):
            existing = self._user_repo.get_by_email(str(dto.email))
            if existing is not None and existing.id != user_id:
                raise DuplicateEntityError("User", str(dto.email))
            user.email = Email(dto.email)
            updated = True

        if dto.is_active is not None and dto.is_active != user.is_active:
            if dto.is_active:
                user.activate()
            else:
                user.deactivate()
            updated = True

        if updated:
            user.updated_at = datetime.now(UTC)

        saved_user = self._user_repo.save(user)

        return UserDTO(
            id=saved_user.id,
            email=str(saved_user.email),
            full_name=saved_user.full_name,
            is_active=saved_user.is_active,
            roles=saved_user.role_names,
            permissions=saved_user.permission_names,
            created_at=saved_user.created_at,
            updated_at=saved_user.updated_at,
        )
