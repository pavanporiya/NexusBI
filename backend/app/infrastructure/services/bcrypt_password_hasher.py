"""Bcrypt password hashing adapter.

Implements the ``IPasswordHasher`` application port using passlib's bcrypt
backend for secure, salted password hashing with constant-time verification.
"""

from __future__ import annotations

from typing import cast

from passlib.context import CryptContext

from app.application.services.interfaces import IPasswordHasher
from app.domain.value_objects.password import Password


class BcryptPasswordHasher(IPasswordHasher):
    """Bcrypt-based password hasher using passlib.

    This adapter enforces domain password strength rules via the ``Password``
    Value Object before hashing, ensuring weak passwords are rejected before
    any cryptographic work is performed.

    Parameters
    ----------
    rounds : int, default=12
        The bcrypt cost factor. Higher values increase security but also
        hash computation time.
    """

    def __init__(self, rounds: int = 12) -> None:
        self._context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=rounds,
        )

    def hash_password(self, password: str) -> str:
        """Hash a raw password after validating strength rules.

        Parameters
        ----------
        password : str
            The raw plaintext password.

        Returns
        -------
        str
            A bcrypt hash string.

        Raises
        ------
        WeakPasswordError
            If the password fails the ``Password`` Value Object validation.
        """
        Password(password)
        return cast(str, self._context.hash(password))

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a bcrypt hash.

        Uses constant-time comparison to prevent timing attacks.

        Parameters
        ----------
        password : str
            The raw plaintext password to verify.
        hashed_password : str
            The stored bcrypt hash to compare against.

        Returns
        -------
        bool
            ``True`` if the password matches the hash.
        """
        return cast(bool, self._context.verify(password, hashed_password))
