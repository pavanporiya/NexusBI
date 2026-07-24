"""Get current user use case.

Retrieves the authenticated user's profile from a valid access token.
"""

from __future__ import annotations

from app.application.dto.auth_dto import UserDTO
from app.application.services.interfaces import ITokenService
from app.core.exceptions import AuthenticationError
from app.domain.repositories.user_repository import IUserRepository


class GetCurrentUserUseCase:
    """Orchestrates access token verification and user profile retrieval."""

    def __init__(
        self,
        user_repository: IUserRepository,
        token_service: ITokenService,
    ) -> None:
        self._user_repo = user_repository
        self._token_service = token_service

    def execute(self, access_token: str) -> UserDTO:
        """Retrieve the current user from a valid access token.

        Parameters
        ----------
        access_token : str
            A signed JWT access token.

        Returns
        -------
        UserDTO
            The authenticated user's profile data.

        Raises
        ------
        AuthenticationError
            If the token is invalid, the user does not exist, or the
            user account is inactive.
        """
        try:
            claims = self._token_service.verify_access_token(access_token)
        except Exception as exc:
            raise AuthenticationError("Invalid access token", detail=str(exc)) from exc

        user_id = claims.get("sub")
        if not user_id:
            raise AuthenticationError("Malformed access token claims")

        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

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
