"""Session domain entity.

Represents a database-backed refresh token session, enabling refresh token rotation
and device tracking without a central in-memory store like Redis in Version 1.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Session:
    """Represents an active user login session linked to a refresh token.

    Attributes
    ----------
    id : str
        Unique session primary key identifier.
    user_id : str
        The foreign key of the User associated with this session.
    token_id : str
        A unique token ID (JTI) embedded in the refresh token to verify rotation.
    refresh_token : str
        The active refresh token string.
    expires_at : datetime
        UTC timestamp when this session's refresh token expires.
    is_revoked : bool
        Flag indicating if the session has been manually revoked or rotated out.
    created_at : datetime
        Timestamp when the session was initialized.
    updated_at : datetime
        Timestamp when the session was last modified.
    client_ip : str | None
        Optional client IP address of the requester.
    user_agent : str | None
        Optional User-Agent string from the client browser.
    """

    id: str
    user_id: str
    token_id: str
    refresh_token: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    client_ip: str | None = None
    user_agent: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the session has exceeded its expiration date."""
        return datetime.now(UTC) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the session is active, unrevoked, and unexpired."""
        return not self.is_revoked and not self.is_expired
