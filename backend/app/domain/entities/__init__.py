"""Domain entities package.

Exposes core business objects: User, Role, Permission, and Session.
"""

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.session import Session
from app.domain.entities.user import User

__all__ = ["Permission", "Role", "Session", "User"]
