"""RBAC Seed Data and Permission Registry for NexusBI.

Provides predefined default roles, permissions, and a central in-memory
PermissionRegistry domain service for querying role-based access control definitions
without database or ORM dependencies.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role

# ----------------------------------------------------------------------
# Predefined Default Permissions
# ----------------------------------------------------------------------

# Users
PERM_USERS_CREATE = Permission(
    id="perm-users-create",
    resource="users",
    action="create",
    description="Create new user accounts",
)
PERM_USERS_READ = Permission(
    id="perm-users-read",
    resource="users",
    action="read",
    description="Read user account details",
)
PERM_USERS_UPDATE = Permission(
    id="perm-users-update",
    resource="users",
    action="update",
    description="Update existing user accounts",
)
PERM_USERS_DELETE = Permission(
    id="perm-users-delete",
    resource="users",
    action="delete",
    description="Delete user accounts",
)

# Roles
PERM_ROLES_CREATE = Permission(
    id="perm-roles-create",
    resource="roles",
    action="create",
    description="Create new RBAC roles",
)
PERM_ROLES_READ = Permission(
    id="perm-roles-read",
    resource="roles",
    action="read",
    description="Read RBAC roles and assigned permissions",
)
PERM_ROLES_UPDATE = Permission(
    id="perm-roles-update",
    resource="roles",
    action="update",
    description="Update RBAC roles and permissions",
)
PERM_ROLES_DELETE = Permission(
    id="perm-roles-delete",
    resource="roles",
    action="delete",
    description="Delete RBAC roles",
)

# Dashboard
PERM_DASHBOARD_VIEW = Permission(
    id="perm-dashboard-view",
    resource="dashboard",
    action="view",
    description="View dashboard analytics and visualizations",
)
PERM_DASHBOARD_READ = Permission(
    id="perm-dashboard-read",
    resource="dashboard",
    action="read",
    description="Read dashboard configuration and raw data",
)
PERM_DASHBOARD_EDIT = Permission(
    id="perm-dashboard-edit",
    resource="dashboard",
    action="edit",
    description="Edit existing dashboard layouts and widgets",
)
PERM_DASHBOARD_CREATE = Permission(
    id="perm-dashboard-create",
    resource="dashboard",
    action="create",
    description="Create new dashboards",
)
PERM_DASHBOARD_UPDATE = Permission(
    id="perm-dashboard-update",
    resource="dashboard",
    action="update",
    description="Update dashboard configurations",
)
PERM_DASHBOARD_DELETE = Permission(
    id="perm-dashboard-delete",
    resource="dashboard",
    action="delete",
    description="Delete dashboards",
)

# Reports
PERM_REPORTS_CREATE = Permission(
    id="perm-reports-create",
    resource="reports",
    action="create",
    description="Create new analytical reports",
)
PERM_REPORTS_READ = Permission(
    id="perm-reports-read",
    resource="reports",
    action="read",
    description="Read and view analytical reports",
)
PERM_REPORTS_UPDATE = Permission(
    id="perm-reports-update",
    resource="reports",
    action="update",
    description="Update report definitions",
)
PERM_REPORTS_DELETE = Permission(
    id="perm-reports-delete",
    resource="reports",
    action="delete",
    description="Delete analytical reports",
)
PERM_REPORTS_EXPORT = Permission(
    id="perm-reports-export",
    resource="reports",
    action="export",
    description="Export report datasets to external formats",
)

# Settings
PERM_SETTINGS_READ = Permission(
    id="perm-settings-read",
    resource="settings",
    action="read",
    description="Read system configuration settings",
)
PERM_SETTINGS_UPDATE = Permission(
    id="perm-settings-update",
    resource="settings",
    action="update",
    description="Update system configuration settings",
)

DEFAULT_PERMISSIONS: tuple[Permission, ...] = (
    PERM_USERS_CREATE,
    PERM_USERS_READ,
    PERM_USERS_UPDATE,
    PERM_USERS_DELETE,
    PERM_ROLES_CREATE,
    PERM_ROLES_READ,
    PERM_ROLES_UPDATE,
    PERM_ROLES_DELETE,
    PERM_DASHBOARD_VIEW,
    PERM_DASHBOARD_READ,
    PERM_DASHBOARD_EDIT,
    PERM_DASHBOARD_CREATE,
    PERM_DASHBOARD_UPDATE,
    PERM_DASHBOARD_DELETE,
    PERM_REPORTS_CREATE,
    PERM_REPORTS_READ,
    PERM_REPORTS_UPDATE,
    PERM_REPORTS_DELETE,
    PERM_REPORTS_EXPORT,
    PERM_SETTINGS_READ,
    PERM_SETTINGS_UPDATE,
)

# ----------------------------------------------------------------------
# Predefined Default Roles
# ----------------------------------------------------------------------


def _create_default_roles() -> tuple[Role, ...]:
    """Factory creating default system roles pre-populated with permissions."""

    # 1. Super Admin: full unrestricted system access
    super_admin = Role(
        id="role-super-admin",
        name="Super Admin",
        description="Full system administrative control with all permissions",
        permissions=list(DEFAULT_PERMISSIONS),
    )

    # 2. Admin: administrative control
    admin = Role(
        id="role-admin",
        name="Admin",
        description="Administrative access to manage users, roles, system settings",
        permissions=[
            PERM_USERS_CREATE,
            PERM_USERS_READ,
            PERM_USERS_UPDATE,
            PERM_USERS_DELETE,
            PERM_ROLES_CREATE,
            PERM_ROLES_READ,
            PERM_ROLES_UPDATE,
            PERM_ROLES_DELETE,
            PERM_DASHBOARD_VIEW,
            PERM_DASHBOARD_READ,
            PERM_DASHBOARD_EDIT,
            PERM_DASHBOARD_CREATE,
            PERM_DASHBOARD_UPDATE,
            PERM_DASHBOARD_DELETE,
            PERM_REPORTS_CREATE,
            PERM_REPORTS_READ,
            PERM_REPORTS_UPDATE,
            PERM_REPORTS_DELETE,
            PERM_REPORTS_EXPORT,
            PERM_SETTINGS_READ,
            PERM_SETTINGS_UPDATE,
        ],
    )

    # 3. Manager: management privileges
    manager = Role(
        id="role-manager",
        name="Manager",
        description="Management access for dashboards, operations, and reporting",
        permissions=[
            PERM_USERS_READ,
            PERM_DASHBOARD_VIEW,
            PERM_DASHBOARD_READ,
            PERM_DASHBOARD_EDIT,
            PERM_DASHBOARD_CREATE,
            PERM_DASHBOARD_UPDATE,
            PERM_REPORTS_CREATE,
            PERM_REPORTS_READ,
            PERM_REPORTS_UPDATE,
            PERM_REPORTS_EXPORT,
            PERM_SETTINGS_READ,
        ],
    )

    # 4. Analyst: data analytical and dashboard editing capabilities
    analyst = Role(
        id="role-analyst",
        name="Analyst",
        description="Analytical access to create, edit dashboards, and export reports",
        permissions=[
            PERM_DASHBOARD_VIEW,
            PERM_DASHBOARD_READ,
            PERM_DASHBOARD_EDIT,
            PERM_DASHBOARD_CREATE,
            PERM_DASHBOARD_UPDATE,
            PERM_REPORTS_CREATE,
            PERM_REPORTS_READ,
            PERM_REPORTS_UPDATE,
            PERM_REPORTS_EXPORT,
        ],
    )

    # 5. Viewer: read-only access for dashboards and reports
    viewer = Role(
        id="role-viewer",
        name="Viewer",
        description="Read-only view access for dashboards and reports",
        permissions=[
            PERM_DASHBOARD_VIEW,
            PERM_DASHBOARD_READ,
            PERM_REPORTS_READ,
        ],
    )

    return (super_admin, admin, manager, analyst, viewer)


DEFAULT_ROLES: tuple[Role, ...] = _create_default_roles()


# ----------------------------------------------------------------------
# Permission Registry
# ----------------------------------------------------------------------


class PermissionRegistry:
    """In-memory domain registry for RBAC default roles and permissions.

    Maintains fast indexes for querying permissions and roles by ID, name,
    qualified name, or resource:action pairs. Enforces uniqueness when
    registering permissions and roles.
    """

    def __init__(
        self,
        roles: Sequence[Role] | None = None,
        permissions: Sequence[Permission] | None = None,
    ) -> None:
        """Initialize registry with optional roles and permissions.

        Parameters
        ----------
        roles : Sequence[Role] | None
            Roles to populate into registry.
        permissions : Sequence[Permission] | None
            Permissions to populate into registry.
        """
        self._permissions_by_qualified_name: dict[str, Permission] = {}
        self._permissions_by_id: dict[str, Permission] = {}
        self._roles_by_name: dict[str, Role] = {}
        self._roles_by_id: dict[str, Role] = {}

        if permissions is not None:
            for perm in permissions:
                self.register_permission(perm)

        if roles is not None:
            for role in roles:
                self.register_role(role)

    def register_permission(self, permission: Permission) -> None:
        """Register a permission in the registry.

        Parameters
        ----------
        permission : Permission
            The domain permission object to register.

        Raises
        ------
        ValueError
            If a permission with the same qualified name or ID is registered.
        """
        if permission.qualified_name in self._permissions_by_qualified_name:
            msg = (
                "Duplicate permission qualified name registered: "
                f"{permission.qualified_name!r}"
            )
            raise ValueError(msg)
        if permission.id in self._permissions_by_id:
            msg = f"Duplicate permission ID registered: {permission.id!r}"
            raise ValueError(msg)

        self._permissions_by_qualified_name[permission.qualified_name] = permission
        self._permissions_by_id[permission.id] = permission

    def register_role(self, role: Role) -> None:
        """Register a role in the registry.

        Parameters
        ----------
        role : Role
            The domain role object to register.

        Raises
        ------
        ValueError
            If a role with the same name or ID is already registered.
        """
        norm_name = self._normalize_name(role.name)
        if norm_name in self._roles_by_name:
            msg = f"Duplicate role name registered: {role.name!r}"
            raise ValueError(msg)
        if role.id in self._roles_by_id:
            msg = f"Duplicate role ID registered: {role.id!r}"
            raise ValueError(msg)

        self._roles_by_name[norm_name] = role
        self._roles_by_id[role.id] = role

    def get_permissions(self) -> list[Permission]:
        """Return all permissions currently registered in the registry."""
        return list(self._permissions_by_qualified_name.values())

    def get_roles(self) -> list[Role]:
        """Return all roles currently registered in the registry."""
        return list(self._roles_by_id.values())

    def find_permission(
        self, qualified_name_or_resource: str, action: str | None = None
    ) -> Permission | None:
        """Find a registered permission by qualified name, (resource, action), or ID.

        Parameters
        ----------
        qualified_name_or_resource : str
            A qualified permission string ('resource:action'), a resource name, or ID.
        action : str | None
            Optional action name when qualified_name_or_resource is a resource.

        Returns
        -------
        Permission | None
            The matching Permission entity or None if missing.
        """
        if action is not None:
            qname = f"{qualified_name_or_resource}:{action}"
            return self._permissions_by_qualified_name.get(qname)

        if ":" in qualified_name_or_resource:
            return self._permissions_by_qualified_name.get(qualified_name_or_resource)

        # Check by ID or qualified name lookup
        if qualified_name_or_resource in self._permissions_by_id:
            return self._permissions_by_id[qualified_name_or_resource]

        return self._permissions_by_qualified_name.get(qualified_name_or_resource)

    def find_role(self, name_or_id: str) -> Role | None:
        """Find a registered role by name or ID.

        Parameters
        ----------
        name_or_id : str
            The role name (e.g. 'Super Admin', 'super_admin') or role ID.

        Returns
        -------
        Role | None
            The matching Role entity or None if missing.
        """
        if name_or_id in self._roles_by_id:
            return self._roles_by_id[name_or_id]

        norm_name = self._normalize_name(name_or_id)
        return self._roles_by_name.get(norm_name)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a role name for case-insensitive and snake_case matching."""
        return name.strip().lower().replace(" ", "_").replace("-", "_")


# Global default registry pre-loaded with default roles and permissions
_DEFAULT_REGISTRY = PermissionRegistry(
    roles=DEFAULT_ROLES, permissions=DEFAULT_PERMISSIONS
)


# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------


def get_default_roles() -> list[Role]:
    """Return copies of all default system roles pre-loaded with permissions."""
    return [copy.deepcopy(r) for r in _DEFAULT_REGISTRY.get_roles()]


def get_default_permissions() -> list[Permission]:
    """Return all default system permissions."""
    return _DEFAULT_REGISTRY.get_permissions()


def find_permission(
    qualified_name_or_resource: str, action: str | None = None
) -> Permission | None:
    """Look up a default permission by qualified name, (resource, action), or ID.

    Returns None if missing.
    """
    return _DEFAULT_REGISTRY.find_permission(qualified_name_or_resource, action)


def find_role(name_or_id: str) -> Role | None:
    """Look up a default role by name or ID.

    Returns None if missing.
    """
    role = _DEFAULT_REGISTRY.find_role(name_or_id)
    return copy.deepcopy(role) if role is not None else None
