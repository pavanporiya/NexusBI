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
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
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


class DashboardModel(Base):
    """ORM model for the ``dashboards`` table.

    Represents a BI dashboard containing widget layout configurations.
    """

    __tablename__ = "dashboards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout_json: Mapped[dict[str, Any]] = mapped_column(
        "layout_json", JSON, nullable=False, default=dict
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    owner: Mapped[UserModel] = relationship("UserModel")
    dataset: Mapped[DatasetModel] = relationship("DatasetModel")

    @property
    def layout_config(self) -> dict[str, Any]:
        """Backward compatibility alias for layout_json."""
        return self.layout_json

    @layout_config.setter
    def layout_config(self, value: dict[str, Any]) -> None:
        """Backward compatibility setter for layout_json."""
        self.layout_json = value

    def __repr__(self) -> str:
        return f"DashboardModel(id={self.id!r}, name={self.name!r})"


class DatasetModel(Base):
    """ORM model for the ``datasets`` table.

    Represents a data source definition, query, or physical table reference.
    """

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    query_or_table: Mapped[str] = mapped_column(Text, nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    object_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    sql_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    connection_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    owner: Mapped[UserModel] = relationship("UserModel")

    def __repr__(self) -> str:
        return f"DatasetModel(id={self.id!r}, name={self.name!r})"


class ReportModel(Base):
    """ORM model for the ``reports`` table.

    Represents an analytical report aggregate configuration.
    """

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="tabular", index=True
    )
    output_format: Mapped[str] = mapped_column(
        String(64), nullable=False, default="json"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schedule: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False, default="")
    visualization_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="table"
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    owner: Mapped[UserModel] = relationship("UserModel")
    dataset: Mapped[DatasetModel] = relationship("DatasetModel")

    def __repr__(self) -> str:
        return f"ReportModel(id={self.id!r}, name={self.name!r})"


class OrganizationModel(Base):
    """ORM model for the ``organizations`` table."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(
        String(256), nullable=False, unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    workspaces: Mapped[list[WorkspaceModel]] = relationship(
        "WorkspaceModel",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"OrganizationModel(id={self.id!r}, slug={self.slug!r})"


class WorkspaceModel(Base):
    """ORM model for the ``workspaces`` table."""

    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "slug", name="uq_workspaces_organization_slug"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    organization: Mapped[OrganizationModel] = relationship(
        "OrganizationModel",
        back_populates="workspaces",
    )
    memberships: Mapped[list[MembershipModel]] = relationship(
        "MembershipModel",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"WorkspaceModel(id={self.id!r}, slug={self.slug!r})"


class MembershipModel(Base):
    """ORM model for the ``memberships`` table."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "user_id", name="uq_memberships_workspace_user"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    workspace: Mapped[WorkspaceModel] = relationship(
        "WorkspaceModel",
        back_populates="memberships",
    )
    user: Mapped[UserModel] = relationship("UserModel")
    role: Mapped[RoleModel] = relationship("RoleModel")

    def __repr__(self) -> str:
        return (
            f"MembershipModel(id={self.id!r}, workspace_id={self.workspace_id!r}, "
            f"user_id={self.user_id!r})"
        )


class WidgetModel(Base):
    """ORM model for the ``widgets`` table.

    Represents a dashboard widget visualization bound to a dataset.
    """

    __tablename__ = "widgets"
    __table_args__ = (
        UniqueConstraint("dashboard_id", "title", name="uq_widgets_dashboard_title"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dashboard_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    widget_type: Mapped[str] = mapped_column(String(64), nullable=False)
    row: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    refresh_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    dashboard: Mapped[DashboardModel] = relationship("DashboardModel")
    dataset: Mapped[DatasetModel] = relationship("DatasetModel")

    def __repr__(self) -> str:
        return (
            f"WidgetModel(id={self.id!r}, title={self.title!r}, "
            f"dashboard_id={self.dashboard_id!r})"
        )
