"""Session repository protocol interface.

Defines the full contract for session persistence, revocation, and cleanup
using :class:`typing.Protocol` for structural sub-typing.

This interface is a strict super-set of the foundational
``app.domain.repositories.session_repository.ISessionRepository`` ABC.
Infrastructure adapters should implement *this* protocol when building
Sprint 2A+ features.

Design Notes
------------
* ``Protocol`` is chosen over ``ABC`` so that any conforming class satisfies
  the contract via structural typing without an explicit inheritance chain.
* Methods use ``async``-free signatures — async wrappers are an
  infrastructure concern and belong in the adapter layer.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities.session import Session


@runtime_checkable
class ISessionRepository(Protocol):
    """Protocol defining the full session persistence contract.

    Methods
    -------
    create(session)
        Persist a new session entity.
    revoke(session_id)
        Mark a session as revoked by its unique identifier.
    find_active(user_id)
        Retrieve all active (non-revoked, non-expired) sessions for a user.
    delete_expired()
        Purge all expired sessions from persistent storage.
    """

    def create(self, session: Session) -> Session:
        """Persist a new session entity.

        Parameters
        ----------
        session : Session
            The fully-constructed session entity to persist.

        Returns
        -------
        Session
            The persisted session entity (may include generated fields).
        """
        ...

    def revoke(self, session_id: str) -> bool:
        """Mark a session as revoked by its unique identifier.

        Parameters
        ----------
        session_id : str
            The UUID of the session to revoke.

        Returns
        -------
        bool
            ``True`` if the session was found and revoked, ``False`` if
            no matching active session existed.
        """
        ...

    def find_active(self, user_id: str) -> list[Session]:
        """Retrieve all active sessions for a user.

        An active session is one that is **not revoked** and **not expired**.

        Parameters
        ----------
        user_id : str
            The UUID of the user whose active sessions to retrieve.

        Returns
        -------
        list[Session]
            Active sessions ordered by creation time (newest first).
            Empty list when the user has no active sessions.
        """
        ...

    def delete_expired(self) -> int:
        """Purge all expired sessions from persistent storage.

        This is a maintenance operation intended to be called by a scheduled
        task to reclaim storage.

        Returns
        -------
        int
            The number of expired session records that were deleted.
        """
        ...
