"""RBAC Database Seed Script for NexusBI.

Populates default RBAC permissions, default system roles (Super Admin, Admin, Editor,
Viewer), role-permission mappings, and assigns the Super Admin role to admin@nexusbi.io
(or the first registered user).

Idempotent and safe to run multiple times during startup or CI/CD pipelines.
"""

from __future__ import annotations

import sys
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import _create_engine, _create_session_factory
from app.core.logging import get_logger
from app.infrastructure.database.models import PermissionModel, RoleModel, UserModel, user_roles

logger = get_logger("nexusbi.rbac_seed")

# ---------------------------------------------------------------------------
# Default Permissions Matrix
# ---------------------------------------------------------------------------

DEFAULT_PERMISSIONS: list[dict[str, str]] = [
    # Organization management
    {"resource": "organizations", "action": "create", "description": "Create new organizations"},
    {"resource": "organizations", "action": "read", "description": "View organization details and lists"},
    {"resource": "organizations", "action": "update", "description": "Update organization settings"},
    {"resource": "organizations", "action": "delete", "description": "Delete organizations"},
    # Workspace management
    {"resource": "workspaces", "action": "create", "description": "Create new workspaces"},
    {"resource": "workspaces", "action": "read", "description": "View workspace details and lists"},
    {"resource": "workspaces", "action": "update", "description": "Update workspace configuration"},
    {"resource": "workspaces", "action": "delete", "description": "Delete workspaces"},
    # Membership management
    {"resource": "memberships", "action": "create", "description": "Add members to workspaces"},
    {"resource": "memberships", "action": "read", "description": "View workspace member lists"},
    {"resource": "memberships", "action": "update", "description": "Update workspace member roles"},
    {"resource": "memberships", "action": "delete", "description": "Remove members from workspaces"},
    # User management
    {"resource": "users", "action": "create", "description": "Create user accounts"},
    {"resource": "users", "action": "read", "description": "View user profiles and user list"},
    {"resource": "users", "action": "update", "description": "Update user account information"},
    {"resource": "users", "action": "delete", "description": "Delete or deactivate user accounts"},
    # Role management
    {"resource": "roles", "action": "create", "description": "Create custom RBAC roles"},
    {"resource": "roles", "action": "read", "description": "View system and custom roles"},
    {"resource": "roles", "action": "update", "description": "Modify role definitions and permissions"},
    {"resource": "roles", "action": "delete", "description": "Delete custom roles"},
    # Dataset management
    {"resource": "datasets", "action": "create", "description": "Register new datasets"},
    {"resource": "datasets", "action": "read", "description": "View datasets and execute queries"},
    {"resource": "datasets", "action": "update", "description": "Update dataset definitions and schemas"},
    {"resource": "datasets", "action": "delete", "description": "Delete datasets"},
    # Dashboard management
    {"resource": "dashboard", "action": "create", "description": "Create new BI dashboards"},
    {"resource": "dashboard", "action": "read", "description": "View dashboards and widgets"},
    {"resource": "dashboard", "action": "update", "description": "Update dashboard definitions and widgets"},
    {"resource": "dashboard", "action": "delete", "description": "Delete dashboards and widgets"},
    # Report management
    {"resource": "reports", "action": "create", "description": "Create analytical reports"},
    {"resource": "reports", "action": "read", "description": "View analytical reports and queries"},
    {"resource": "reports", "action": "update", "description": "Modify analytical reports"},
    {"resource": "reports", "action": "delete", "description": "Delete analytical reports"},
    # Connector management
    {"resource": "connectors", "action": "create", "description": "Create data source connectors"},
    {"resource": "connectors", "action": "read", "description": "Discover and inspect connectors"},
    {"resource": "connectors", "action": "update", "description": "Modify connector configurations"},
    {"resource": "connectors", "action": "delete", "description": "Delete data source connectors"},
]

# ---------------------------------------------------------------------------
# Default Roles & Permission Mappings
# ---------------------------------------------------------------------------

ALL_PERMISSION_PAIRS = [(p["resource"], p["action"]) for p in DEFAULT_PERMISSIONS]

EDITOR_PERMISSION_PAIRS = [
    ("organizations", "read"),
    ("workspaces", "create"),
    ("workspaces", "read"),
    ("workspaces", "update"),
    ("memberships", "create"),
    ("memberships", "read"),
    ("memberships", "update"),
    ("users", "read"),
    ("roles", "read"),
    ("datasets", "create"),
    ("datasets", "read"),
    ("datasets", "update"),
    ("dashboard", "create"),
    ("dashboard", "read"),
    ("dashboard", "update"),
    ("reports", "create"),
    ("reports", "read"),
    ("reports", "update"),
    ("connectors", "create"),
    ("connectors", "read"),
    ("connectors", "update"),
]

VIEWER_PERMISSION_PAIRS = [
    ("organizations", "read"),
    ("workspaces", "read"),
    ("memberships", "read"),
    ("users", "read"),
    ("roles", "read"),
    ("datasets", "read"),
    ("dashboard", "read"),
    ("reports", "read"),
    ("connectors", "read"),
]

DEFAULT_ROLES: list[dict[str, Any]] = [
    {
        "name": "Super Admin",
        "description": "Full unrestricted administrative access to all system resources and permissions.",
        "permissions": ALL_PERMISSION_PAIRS,
    },
    {
        "name": "Admin",
        "description": "Administrative access to manage users, organizations, workspaces, datasets, dashboards, reports, and connectors.",
        "permissions": ALL_PERMISSION_PAIRS,
    },
    {
        "name": "Editor",
        "description": "Can create and edit workspaces, datasets, dashboards, reports, and connectors.",
        "permissions": EDITOR_PERMISSION_PAIRS,
    },
    {
        "name": "Viewer",
        "description": "Read-only access to system dashboards, reports, datasets, and workspaces.",
        "permissions": VIEWER_PERMISSION_PAIRS,
    },
]


def seed_rbac(session: Session) -> None:
    """Seed default permissions, roles, role-permission mappings, and super admin user assignment.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """
    logger.info("Starting RBAC database seed")

    # 1. Seed Permissions
    existing_perms = session.execute(select(PermissionModel)).scalars().all()
    perm_map: dict[tuple[str, str], PermissionModel] = {
        (p.resource, p.action): p for p in existing_perms
    }

    created_perms_count = 0
    for perm_def in DEFAULT_PERMISSIONS:
        key = (perm_def["resource"], perm_def["action"])
        if key not in perm_map:
            perm_model = PermissionModel(
                id=str(uuid.uuid4()),
                resource=perm_def["resource"],
                action=perm_def["action"],
                description=perm_def["description"],
            )
            session.add(perm_model)
            perm_map[key] = perm_model
            created_perms_count += 1

    session.flush()
    logger.info(
        "Permissions seeded",
        total_permissions=len(perm_map),
        newly_created=created_perms_count,
    )

    # 2. Seed Roles & Role-Permissions
    existing_roles = session.execute(select(RoleModel)).scalars().all()
    role_map: dict[str, RoleModel] = {r.name: r for r in existing_roles}

    created_roles_count = 0
    for role_def in DEFAULT_ROLES:
        role_name = role_def["name"]
        role_model = role_map.get(role_name)
        if not role_model:
            role_model = RoleModel(
                id=str(uuid.uuid4()),
                name=role_name,
                description=role_def["description"],
            )
            session.add(role_model)
            role_map[role_name] = role_model
            created_roles_count += 1
        else:
            role_model.description = role_def["description"]

        # Map target permissions
        target_perms = [
            perm_map[pair] for pair in role_def["permissions"] if pair in perm_map
        ]
        role_model.permissions = target_perms

    session.flush()
    logger.info(
        "Roles and role-permissions seeded",
        total_roles=len(role_map),
        newly_created=created_roles_count,
    )

    # 3. Assign Super Admin role to default admin user or first user if no admin exists
    super_admin_role = role_map.get("Super Admin")
    if super_admin_role:
        # Check if any user is currently assigned the Super Admin role
        assigned_user_ids = list(
            session.execute(
                select(user_roles.c.user_id).where(
                    user_roles.c.role_id == super_admin_role.id
                )
            )
            .scalars()
            .all()
        )

        if not assigned_user_ids:
            # Find admin@nexusbi.io first, otherwise fallback to first registered user
            target_user = (
                session.execute(
                    select(UserModel).where(UserModel.email == "admin@nexusbi.io")
                )
                .scalars()
                .first()
            )

            if not target_user:
                target_user = (
                    session.execute(
                        select(UserModel).order_by(UserModel.created_at.asc())
                    )
                    .scalars()
                    .first()
                )

            if target_user:
                if super_admin_role not in target_user.roles:
                    target_user.roles.append(super_admin_role)
                    session.flush()
                    logger.info(
                        "Assigned Super Admin role to user",
                        user_id=target_user.id,
                        email=target_user.email,
                    )
        else:
            logger.info(
                "Super Admin role already assigned to users",
                count=len(assigned_user_ids),
            )

    session.commit()
    logger.info("RBAC database seed completed successfully")


def run_seed() -> None:
    """CLI runner to execute seed_rbac against configured database."""
    settings = get_settings()
    engine = _create_engine(settings)
    session_factory = _create_session_factory(engine)

    with session_factory() as session:
        try:
            seed_rbac(session)
        except Exception as exc:
            session.rollback()
            logger.error("Failed to seed RBAC database", error=str(exc))
            sys.exit(1)


if __name__ == "__main__":
    run_seed()
