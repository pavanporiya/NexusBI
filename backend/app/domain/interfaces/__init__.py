"""Domain interfaces package.

Exposes Protocol-based repository contracts for the authentication domain.
These interfaces extend the foundational ABC contracts in
``app.domain.repositories`` with additional query and lifecycle methods
required by Sprint 2A.
"""

from app.domain.interfaces.i_session_repository import ISessionRepository
from app.domain.interfaces.i_user_repository import IUserRepository

__all__ = ["ISessionRepository", "IUserRepository"]
