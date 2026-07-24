"""Session entity ↔ ORM model mapper.

Provides bidirectional conversion between ``app.domain.entities.Session``
and ``app.infrastructure.database.models.SessionModel``.
"""

from __future__ import annotations

from app.domain.entities.session import Session
from app.infrastructure.database.models import SessionModel


class SessionMapper:
    """Stateless mapper between Session domain entities and SessionModel ORM objects."""

    @staticmethod
    def to_domain(model: SessionModel) -> Session:
        """Convert a ``SessionModel`` ORM instance to a ``Session`` domain entity.

        Parameters
        ----------
        model : SessionModel
            The SQLAlchemy model to convert.

        Returns
        -------
        Session
            A fully-hydrated domain entity.
        """
        return Session(
            id=model.id,
            user_id=model.user_id,
            token_id=model.token_id,
            refresh_token=model.refresh_token,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
            revoked_at=model.revoked_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            client_ip=model.client_ip,
            user_agent=model.user_agent,
        )

    @staticmethod
    def to_model(entity: Session) -> SessionModel:
        """Convert a ``Session`` domain entity to a new ``SessionModel`` instance.

        Parameters
        ----------
        entity : Session
            The domain entity to convert.

        Returns
        -------
        SessionModel
            A new ORM model instance ready for persistence.
        """
        return SessionModel(
            id=entity.id,
            user_id=entity.user_id,
            token_id=entity.token_id,
            refresh_token=entity.refresh_token,
            expires_at=entity.expires_at,
            is_revoked=entity.is_revoked,
            revoked_at=entity.revoked_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            client_ip=entity.client_ip,
            user_agent=entity.user_agent,
        )

    @staticmethod
    def update_model(model: SessionModel, entity: Session) -> SessionModel:
        """Patch an existing ``SessionModel`` with values from a domain entity.

        Parameters
        ----------
        model : SessionModel
            The existing ORM model to update in-place.
        entity : Session
            The domain entity containing updated values.

        Returns
        -------
        SessionModel
            The same model instance, mutated in-place.
        """
        model.token_id = entity.token_id
        model.refresh_token = entity.refresh_token
        model.expires_at = entity.expires_at
        model.is_revoked = entity.is_revoked
        model.revoked_at = entity.revoked_at
        model.updated_at = entity.updated_at
        model.client_ip = entity.client_ip
        model.user_agent = entity.user_agent
        return model
