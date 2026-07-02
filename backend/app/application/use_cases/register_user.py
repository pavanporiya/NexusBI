"""Register user use case.

Handles user sign-up logic and initial persistence.
"""

import uuid

from app.application.dto.auth_dto import RegisterDTO, UserDTO
from app.application.services.interfaces import IPasswordHasher
from app.core.exceptions import DuplicateEntityError
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository


class RegisterUserUseCase:
    """Orchestrates registration of new password-authenticated users."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
    ) -> None:
        self._user_repo = user_repository
        self._hasher = password_hasher

    def execute(self, dto: RegisterDTO) -> UserDTO:
        """Register a new user in the system.

        Raises
        ------
        DuplicateEntityError
            If the email is already registered.
        """
        existing = self._user_repo.get_by_email(dto.email)
        if existing is not None:
            raise DuplicateEntityError("User", str(dto.email))

        # Generate unique ID and hash password
        user_id = str(uuid.uuid4())
        hashed = self._hasher.hash_password(dto.password)

        new_user = User(
            id=user_id,
            email=str(dto.email),
            hashed_password=hashed,
            is_active=True,
        )

        saved_user = self._user_repo.save(new_user)

        return UserDTO(
            id=saved_user.id,
            email=saved_user.email,
            is_active=saved_user.is_active,
            roles=saved_user.role_names,
            permissions=saved_user.permission_names,
            created_at=saved_user.created_at,
            updated_at=saved_user.updated_at,
        )
class_name = "RegisterUserUseCase"
