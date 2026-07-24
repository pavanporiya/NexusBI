"""Role Data Transfer Objects (DTOs).

Defines serialization and type boundaries for Role and Permission application
layer outputs. Uses Pydantic v2.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PermissionDTO(BaseModel):
    """Permission detail data contract."""

    id: str
    resource: str
    action: str
    description: str | None = None


class RoleDTO(BaseModel):
    """Role detail data contract."""

    id: str
    name: str
    description: str | None = None
    permissions: list[PermissionDTO] = Field(default_factory=list)


class CreateRoleDTO(BaseModel):
    """Data contract for creating a new role."""

    name: str = Field(
        ..., min_length=1, max_length=128, description="Unique name of the role"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Optional description of the role"
    )
    permission_ids: list[str] = Field(
        default_factory=list,
        description="List of permission IDs to assign to the role",
    )


class UpdateRoleDTO(BaseModel):
    """Data contract for updating an existing role."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Updated name of the role",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated description of the role",
    )
    permission_ids: list[str] | None = Field(
        default=None,
        description="Updated list of permission IDs to assign to the role",
    )
