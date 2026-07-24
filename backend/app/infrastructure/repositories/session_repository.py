"""SQLAlchemy implementation of the Session repository.

Fulfills the ``ISessionRepository`` ABC contract defined in the domain layer.
SQLAlchemy models are never exposed outside this module — all public methods
accept and return domain entities exclusively.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DBSession

from app.domain.entities.session import Session
from app.domain.repositories.session_repository import ISessionRepository
from app.infrastructure.database.models import SessionModel
from app.infrastructure.mappers.session_mapper import SessionMapper


class SQLAlchemySessionRepository(ISessionRepository):
    """Concrete ``ISessionRepository`` backed by SQLAlchemy/PostgreSQL.

    Inherits from ``ISessionRepository`` (ABC) to satisfy the nominal
    typing contract.

    Parameters
    ----------
    session : DBSession
        An active SQLAlchemy session (unit of work).
    """

    def __init__(self, session: DBSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # ISessionRepository contract
    # ------------------------------------------------------------------

    def get_by_id(self, session_id: str) -> Session | None:
        """Fetch a Session by its primary key ID."""
        model = self._session.get(SessionModel, session_id)
        return SessionMapper.to_domain(model) if model else None

    def get_by_token_id(self, token_id: str) -> Session | None:
        """Fetch a Session by its associated refresh token ID (JTI)."""
        stmt = select(SessionModel).where(SessionModel.token_id == token_id)
        model = self._session.execute(stmt).scalars().first()
        return SessionMapper.to_domain(model) if model else None

    def get_by_refresh_token(self, refresh_token: str) -> Session | None:
        """Fetch a Session by its raw refresh token string."""
        stmt = select(SessionModel).where(SessionModel.refresh_token == refresh_token)
        model = self._session.execute(stmt).scalars().first()
        return SessionMapper.to_domain(model) if model else None

    def save(self, session: Session) -> Session:
        """Persist a new Session or update an existing one (upsert)."""
        existing = self._session.get(SessionModel, session.id)

        if existing:
            SessionMapper.update_model(existing, session)
            model = existing
        else:
            model = SessionMapper.to_model(session)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return SessionMapper.to_domain(model)

    def revoke_by_id(self, session_id: str) -> bool:
        """Mark a specific Session as revoked by its primary key."""
        model = self._session.get(SessionModel, session_id)
        if model is None or model.is_revoked:
            return False
        now = datetime.now(UTC)
        model.is_revoked = True
        model.revoked_at = now
        model.updated_at = now
        self._session.flush()
        return True

    def revoke_by_token_id(self, token_id: str) -> bool:
        """Mark a specific Session as revoked using its refresh token ID (JTI)."""
        stmt = select(SessionModel).where(SessionModel.token_id == token_id)
        model = self._session.execute(stmt).scalars().first()
        if model is None or model.is_revoked:
            return False
        now = datetime.now(UTC)
        model.is_revoked = True
        model.revoked_at = now
        model.updated_at = now
        self._session.flush()
        return True

    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Mark all active sessions for a user as revoked.

        Returns the number of sessions that were revoked.
        """
        now = datetime.now(UTC)
        stmt = (
            update(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.is_revoked.is_(False),
            )
            .values(
                is_revoked=True,
                revoked_at=now,
                updated_at=now,
            )
        )
        cursor_result = self._session.execute(stmt)
        self._session.flush()
        return int(cursor_result.rowcount)  # type: ignore[attr-defined]
