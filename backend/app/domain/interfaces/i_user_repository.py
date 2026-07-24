"""User repository protocol interface.

Defines the full contract for user persistence, retrieval, and RBAC queries
using :class:`typing.Protocol` for structural sub-typing.

This interface is a strict super-set of the foundational
``app.domain.repositories.user_repository.IUserRepository`` ABC.
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

from app.domain.entities.role import Role
from app.domain.entities.user import User


@runtime_checkable
class IUserRepository(Protocol):
    """Protocol defining the full user persistence contract.

    Methods
    -------
    create(user)
        Persist a new user entity. Must raise on duplicate email.
    update(user)
        Apply mutations of an existing user entity to persistent storage.
    delete(user_id)
        Permanently remove a user by their unique identifier.
    find_by_email(email)
        Look up a user by their unique email address.
    find_by_id(user_id)
        Look up a user by their unique identifier.
    exists(email)
        Check whether a user with the given email already exists.
    list_roles(user_id)
        Return all RBAC roles assigned to a user.
    """

    def create(self, user: User) -> User:
        """Persist a new user entity.

        Parameters
        ----------
        user : User
            The fully-constructed user entity to persist.

        Returns
        -------
        User
            The persisted user entity (may include generated fields).

        Raises
        ------
        DuplicateEntityError
            If a user with the same email already exists.
        """
        ...

    def update(self, user: User) -> User:
        """Apply mutations of an existing user entity to storage.

        Parameters
        ----------
        user : User
            The mutated user entity whose state should be persisted.

        Returns
        -------
        User
            The updated user entity.

        Raises
        ------
        EntityNotFoundError
            If no user with the given ``id`` exists.
        """
        ...

    def delete(self, user_id: str) -> bool:
        """Permanently remove a user by their unique identifier.

        Parameters
        ----------
        user_id : str
            The UUID of the user to delete.

        Returns
        -------
        bool
            ``True`` if the user was found and deleted, ``False`` otherwise.
        """
        ...

    def find_by_email(self, email: str) -> User | None:
        """Look up a user by their unique email address.

        Parameters
        ----------
        email : str
            The email address to search for.

        Returns
        -------
        User | None
            The matching user entity, or ``None`` if not found.
        """
        ...

    def find_by_id(self, user_id: str) -> User | None:
        """Look up a user by their unique identifier.

        Parameters
        ----------
        user_id : str
            The UUID of the user.

        Returns
        -------
        User | None
            The matching user entity, or ``None`` if not found.
        """
        ...

    def exists(self, email: str) -> bool:
        """Check whether a user with the given email already exists.

        Parameters
        ----------
        email : str
            The email address to check.

        Returns
        -------
        bool
            ``True`` if a user with this email is present in storage.
        """
        ...

    def list_roles(self, user_id: str) -> list[Role]:
        """Return all RBAC roles assigned to a user.

        Parameters
        ----------
        user_id : str
            The UUID of the user whose roles to retrieve.

        Returns
        -------
        list[Role]
            The list of roles assigned to the user.  Empty list when the
            user has no roles or does not exist.
        """
        ...
