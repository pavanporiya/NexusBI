"""List Users Use Case."""

from __future__ import annotations

from app.application.dto.auth_dto import UserDTO
from app.domain.repositories.user_repository import IUserRepository


class ListUsersUseCase:
    """Fetch a paginated list of all users."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repo = user_repository

    def execute(self, limit: int = 50, offset: int = 0) -> list[UserDTO]:
        users = self._user_repo.list_all(limit=limit, offset=offset)
        return [
            UserDTO(
                id=u.id,
                email=str(u.email),
                full_name=u.full_name,
                is_active=u.is_active,
                roles=u.role_names,
                permissions=u.permission_names,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in users
        ]
