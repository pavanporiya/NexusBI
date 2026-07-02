"""Refresh token use case.

Implements refresh token rotation (RTR) and automatic session revocation on token reuse.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.application.dto.auth_dto import TokenDTO, TokenRefreshDTO
from app.application.services.interfaces import ITokenService
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.domain.entities.session import Session
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.user_repository import IUserRepository


class RefreshTokenUseCase:
    """Orchestrates token rotation checks and reuse detection."""

    def __init__(
        self,
        user_repository: IUserRepository,
        session_repository: ISessionRepository,
        token_service: ITokenService,
    ) -> None:
        self._user_repo = user_repository
        self._session_repo = session_repository
        self._token_service = token_service
        self._settings = get_settings()

    def execute(
        self,
        dto: TokenRefreshDTO,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenDTO:
        """Perform refresh token rotation.

        Raises
        ------
        AuthenticationError
            If token is invalid, expired, revoked, or reuse is detected.
        """
        try:
            claims = self._token_service.verify_refresh_token(dto.refresh_token)
        except Exception as exc:
            raise AuthenticationError("Invalid refresh token", detail=str(exc)) from exc

        token_id = claims.get("jti")
        user_id = claims.get("sub")
        if not token_id or not user_id:
            raise AuthenticationError("Malformed refresh token claims")

        session = self._session_repo.get_by_token_id(token_id)

        # ── Reuse Detection ──────────────────────────────────────────────
        # If session is found but already revoked, it suggests this token
        # has been reused (e.g. re-played by an attacker).
        # We must immediately invalidate all sessions for this user.
        if session is not None and session.is_revoked:
            self._session_repo.revoke_all_user_sessions(user_id)
            raise AuthenticationError(
                "Compromised credentials session refresh rejected",
                detail=(
                    "Token reuse detected. All active user sessions "
                    "have been terminated."
                ),
            )

        if session is None or not session.is_valid:
            raise AuthenticationError("Session is invalid or expired")

        user = self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Associated user account is inactive")

        # ── Perform Rotation ─────────────────────────────────────────────
        # 1. Revoke the old session
        self._session_repo.revoke_by_token_id(token_id)

        # 2. Generate new token pair
        new_access_token = self._token_service.create_access_token(
            subject=user.id,
            roles=user.role_names,
        )

        new_token_id = str(uuid.uuid4())
        new_refresh_token = self._token_service.create_refresh_token(
            subject=user.id,
            token_id=new_token_id,
        )

        # 3. Save new session in database
        expiry = datetime.now(UTC) + timedelta(
            days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_session = Session(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_id=new_token_id,
            refresh_token=new_refresh_token,
            expires_at=expiry,
            client_ip=client_ip or session.client_ip,
            user_agent=user_agent or session.user_agent,
        )
        self._session_repo.save(new_session)

        return TokenDTO(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
class_name = "RefreshTokenUseCase"
