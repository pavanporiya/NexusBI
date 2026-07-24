"""Email Value Object.

Enforces email domain invariants including non-emptiness, format validation,
and lowercase normalization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.exceptions import InvalidEmailError

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True, slots=True)
class Email:
    """Immutable Email Value Object with automatic lowercase normalization.

    Attributes
    ----------
    value : str
        Normalized lowercase email address string.
    """

    value: str

    def __init__(self, value: str | Email) -> None:
        """Construct and validate an Email Value Object.

        Parameters
        ----------
        value : str | Email
            The raw email string or existing Email object.

        Raises
        ------
        InvalidEmailError
            If value is empty, not a string/Email, or does not match email format.
        """
        if isinstance(value, Email):
            object.__setattr__(self, "value", value.value)
            return

        if not isinstance(value, str):
            raise InvalidEmailError("User email must be a string")

        normalized = value.strip().lower()
        if not normalized:
            raise InvalidEmailError("User email must not be empty")

        if not _EMAIL_REGEX.match(normalized):
            raise InvalidEmailError(f"Invalid email address format: '{value}'")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Email({self.value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().lower()
        return False

    def __hash__(self) -> int:
        return hash(self.value)
