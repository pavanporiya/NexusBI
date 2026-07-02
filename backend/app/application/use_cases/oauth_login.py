"""Google OAuth login use case.

Exchanges OAuth credentials with Google and returns user tokens.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.application.dto.auth_dto import TokenDTO
from app.application.services.interfaces import IGoogleOAuthService, ITokenService
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.domain.entities.session import Session
from app.domain.entities.user import User
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.user_repository import IUserRepository


class OAuthLoginUseCase:
    """Orchestrates Google OIDC token exchanges and user linking."""

    def __init__(
        self,
        user_repository: IUserRepository,
        session_repository: ISessionRepository,
        oauth_service: IGoogleOAuthService,
        token_service: ITokenService,
    ) -> None:
        self._user_repo = user_repository
        self._session_repo = session_repository
        self._oauth_service = oauth_service
        self._token_service = token_service
        self._settings = get_settings()

    def execute(
        self,
        code: str,
        redirect_uri: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenDTO:
        """Authenticate user profile obtained from Google OAuth.

        Raises
        ------
        AuthenticationError
            If OAuth validation fails or the account is disabled.
        """
        try:
            google_profile = self._oauth_service.verify_auth_code(code, redirect_uri)
        except Exception as exc:
            raise AuthenticationError(
                "Google OAuth verification failed", detail=str(exc)
            ) from exc

        # 1. Retrieve user by Google ID or Email
        user = self._user_repo.get_by_google_id(google_profile.google_id)
        if user is None:
            user = self._user_repo.get_by_email(google_profile.email)

            if user is None:
                # ── Register New OAuth User ──────────────────────────────
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=str(google_profile.email),
                    google_id=google_profile.google_id,
                    is_active=True,
                )
                user = self._user_repo.save(user)
            else:
                # ── Link Google ID to existing account ───────────────────
                user.google_id = google_profile.google_id
                user.updated_at = datetime.now(UTC)
                user = self._user_repo.save(user)

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # 2. Establish token session
        access_token = self._token_service.create_access_token(
            subject=user.id,
            roles=user.role_names,
        )

        token_id = str(uuid.uuid4())
        refresh_token = self._token_service.create_refresh_token(
            subject=user.id,
            token_id=token_id,
        )

        expiry = datetime.now(UTC) + timedelta(
            days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_id=token_id,
            refresh_token=refresh_token,
            expires_at=expiry,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        self._session_repo.save(session)

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


class_name = "OAuthLoginUseCase"
