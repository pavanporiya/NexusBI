"""Domain exception definitions for NexusBI.

Provides specialized domain exception types extending DomainValidationError (which
inherits from ValueError) to maintain full backwards compatibility while allowing
callers to handle specific domain failures.
"""

from __future__ import annotations


class DomainValidationError(ValueError):
    """Base exception for all domain validation failures.

    Inherits from ValueError for backwards compatibility with legacy callers.
    """


class InvalidEmailError(DomainValidationError):
    """Raised when an email address format or value is invalid."""


class WeakPasswordError(DomainValidationError):
    """Raised when a raw password fails complexity validation rules."""


class InvalidRoleError(DomainValidationError):
    """Raised when a role name or configuration is invalid."""


class UserValidationError(DomainValidationError):
    """Raised when user domain invariants are violated."""


class InvalidQueryError(DomainValidationError):
    """Raised when a query fails validation, syntax, or security checks."""


class QueryTimeoutError(DomainValidationError):
    """Raised when a query execution times out."""


class QueryExecutionError(DomainValidationError):
    """Raised when a query execution fails."""


class ChartValidationError(DomainValidationError):
    """Raised when chart configuration or data fails chart validation rules."""
