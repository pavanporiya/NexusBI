"""Logout user use case.

Revokes a user's session.
"""

from app.application.services.interfaces import ITokenService
from app.core.exceptions import AuthenticationError
from app.domain.repositories.session_repository import ISessionRepository


class LogoutUserUseCase:
    """Orchestrates session revocation to log out a user."""

    def __init__(
        self,
        session_repository: ISessionRepository,
        token_service: ITokenService,
    ) -> None:
        self._session_repo = session_repository
        self._token_service = token_service

    def execute(self, refresh_token: str) -> None:
        """Revoke the session associated with the refresh token."""
        try:
            claims = self._token_service.verify_refresh_token(refresh_token)
            token_id = claims.get("jti")
            if not token_id:
                raise AuthenticationError("Invalid refresh token claims")

            self._session_repo.revoke_by_token_id(token_id)
        except Exception as exc:
            # Re-raise as AuthenticationError to maintain consistent boundaries
            raise AuthenticationError(
                "Failed to process logout session revocation",
                detail=str(exc),
            ) from exc
class_name = "LogoutUserUseCase"
