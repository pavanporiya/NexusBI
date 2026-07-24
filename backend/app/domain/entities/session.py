"""Session domain entity.

Represents a database-backed refresh token session, enabling refresh token
rotation and device tracking without a central in-memory store like Redis
in Version 1.

This is a **rich domain entity** with lifecycle methods that enforce
revocation and expiry invariants.

Business Rules
--------------
* A session is **active** when it has not been revoked and has not expired.
* Revoking an already-revoked session is a safe idempotent no-op.
* ``is_expired`` evaluates against the current UTC wall clock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
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
    revoked_at : datetime | None
        UTC timestamp when the session was revoked, or ``None`` if still active.
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
    revoked_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    client_ip: str | None = None
    user_agent: str | None = None

    # ------------------------------------------------------------------
    # Lifecycle mutations
    # ------------------------------------------------------------------

    def revoke(self) -> None:
        """Mark this session as revoked.

        Idempotent — calling on an already-revoked session is a no-op.
        Sets both ``is_revoked`` and ``revoked_at``.
        """
        if not self.is_revoked:
            self.is_revoked = True
            now = datetime.now(UTC)
            self.revoked_at = now
            self.updated_at = now

    # ------------------------------------------------------------------
    # Query predicates
    # ------------------------------------------------------------------

    @property
    def is_expired(self) -> bool:
        """Check if the session has exceeded its expiration timestamp.

        Returns
        -------
        bool
            ``True`` if the current UTC time is at or past ``expires_at``.
        """
        return datetime.now(UTC) >= self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if the session is currently usable.

        A session is active when it is both **not revoked** and **not expired**.

        Returns
        -------
        bool
            ``True`` if the session can still be used.
        """
        return not self.is_revoked and not self.is_expired

    # ------------------------------------------------------------------
    # Backward-compatible alias
    # ------------------------------------------------------------------

    @property
    def is_valid(self) -> bool:
        """Alias for ``is_active`` to maintain Phase 1 compatibility."""
        return self.is_active

    def __repr__(self) -> str:
        return (
            f"Session(id={self.id!r}, user_id={self.user_id!r}, "
            f"is_active={self.is_active})"
        )
