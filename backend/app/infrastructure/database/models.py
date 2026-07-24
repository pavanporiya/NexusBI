"""SQLAlchemy 2.0 ORM models for the NexusBI persistence layer.

These models are **internal to the Infrastructure layer** and must never be
imported by Domain or Application code. Use the mapper classes in
``app.infrastructure.mappers`` to convert between domain entities and ORM
models.

Tables
------
- ``permissions``  — RBAC permission definitions
- ``roles``        — RBAC role definitions
- ``role_permissions`` — M2M join: roles ↔ permissions
- ``users``        — System user accounts
- ``user_roles``   — M2M join: users ↔ roles
- ``sessions``     — Refresh-token sessions
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

# ---------------------------------------------------------------------------
# Association tables (M2M joins)
# ---------------------------------------------------------------------------

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        String(36),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------


class PermissionModel(Base):
    """ORM model for the ``permissions`` table.

    Represents a discrete RBAC permission identified by a
    ``(resource, action)`` pair.
    """

    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resource: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Back-reference from RoleModel (populated via role_permissions M2M)
    roles: Mapped[list[RoleModel]] = relationship(
        "RoleModel",
        secondary=role_permissions,
        back_populates="permissions",
    )

    def __repr__(self) -> str:
        return (
            f"PermissionModel(id={self.id!r}, "
            f"resource={self.resource!r}, action={self.action!r})"
        )


class RoleModel(Base):
    """ORM model for the ``roles`` table.

    Represents an RBAC role containing a set of permissions.
    """

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    permissions: Mapped[list[PermissionModel]] = relationship(
        "PermissionModel",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )

    # Back-reference from UserModel (populated via user_roles M2M)
    users: Mapped[list[UserModel]] = relationship(
        "UserModel",
        secondary=user_roles,
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"RoleModel(id={self.id!r}, name={self.name!r})"


class UserModel(Base):
    """ORM model for the ``users`` table.

    Represents a system user account with optional OAuth linkage.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    google_id: Mapped[str | None] = mapped_column(
        String(256), nullable=True, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    roles: Mapped[list[RoleModel]] = relationship(
        "RoleModel",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    sessions: Mapped[list[SessionModel]] = relationship(
        "SessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"UserModel(id={self.id!r}, email={self.email!r})"


class SessionModel(Base):
    """ORM model for the ``sessions`` table.

    Represents a refresh-token session bound to a specific user.
    """

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_id: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    refresh_token: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="sessions",
    )

    def __repr__(self) -> str:
        return (
            f"SessionModel(id={self.id!r}, user_id={self.user_id!r}, "
            f"is_revoked={self.is_revoked!r})"
        )
