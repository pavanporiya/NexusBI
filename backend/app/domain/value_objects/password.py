"""Password Value Object.

Enforces password strength rules on raw unhashed passwords. Does not perform hashing.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import WeakPasswordError

_SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;:'\",.<>?/\\`~")


@dataclass(frozen=True, slots=True)
class Password:
    """Immutable Password Value Object enforcing complexity rules.

    Attributes
    ----------
    value : str
        The validated raw password.
    """

    value: str

    def __init__(self, value: str, min_length: int = 8) -> None:
        """Construct and validate a Password Value Object.

        Parameters
        ----------
        value : str
            The raw unhashed password.
        min_length : int, default=8
            The minimum required character length.

        Raises
        ------
        WeakPasswordError
            If password fails complexity validation.
        """
        if not isinstance(value, str):
            raise WeakPasswordError("Password must be a string")

        if len(value) < min_length:
            raise WeakPasswordError(
                f"Password must be at least {min_length} characters long"
            )

        if not any(c.isupper() for c in value):
            raise WeakPasswordError(
                "Password must contain at least one uppercase letter"
            )

        if not any(c.islower() for c in value):
            raise WeakPasswordError(
                "Password must contain at least one lowercase letter"
            )

        if not any(c.isdigit() for c in value):
            raise WeakPasswordError("Password must contain at least one digit")

        if not any(c in _SPECIAL_CHARS for c in value):
            raise WeakPasswordError(
                "Password must contain at least one special character"
            )

        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return "********"

    def __repr__(self) -> str:
        return "Password(********)"
