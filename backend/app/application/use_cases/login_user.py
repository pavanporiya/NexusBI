"""Login user use case.

Orchestrates user authentication via credentials and establishes active sessions.
"""

from datetime import datetime, timedelta, timezone
import uuid

from app.application.dto.auth_dto import LoginDTO, TokenDTO
from app.application.services.interfaces import IPasswordHasher, ITokenService
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.domain.entities.session import Session
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.user_repository import IUserRepository


class LoginUserUseCase:
    """Orchestrates authentication checks and session establishment."""

    def __init__(
        self,
        user_repository: IUserRepository,
        session_repository: ISessionRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ) -> None:
        self._user_repo = user_repository
        self._session_repo = session_repository
        self._hasher = password_hasher
        self._token_service = token_service
        self._settings = get_settings()

    def execute(
        self,
        dto: LoginDTO,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenDTO:
        """Authenticate user credentials and create a session.

        Raises
        ------
        AuthenticationError
            If credentials are invalid or user is inactive.
        """
        user = self._user_repo.get_by_email(dto.email)
        if user is None or user.hashed_password is None:
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        if not self._hasher.verify_password(dto.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # Generate tokens
        access_token = self._token_service.create_access_token(
            subject=user.id,
            roles=user.role_names,
        )

        token_id = str(uuid.uuid4())
        refresh_token = self._token_service.create_refresh_token(
            subject=user.id,
            token_id=token_id,
        )

        # Create refresh token session in database
        expiry = datetime.now(timezone.utc) + timedelta(
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
class_name = "LoginUserUseCase"
