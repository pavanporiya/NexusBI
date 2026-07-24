"""Domain value objects package.

Exposes immutable Value Objects: Email and Password.
"""

from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password

__all__ = ["Email", "Password"]
