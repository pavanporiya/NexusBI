"""Role Data Transfer Objects (DTOs).

Defines serialization and type boundaries for Role and Permission application
layer outputs. Uses Pydantic v2.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PermissionDTO(BaseModel):
    """Permission detail data contract."""

    id: str = Field(
        ...,
        description="Unique permission entity identifier",
        examples=["perm_01HGBX1234567890ABCDEFGH"],
    )
    resource: str = Field(
        ...,
        description="Target system domain resource identifier",
        examples=["users"],
    )
    action: str = Field(
        ...,
        description="Permitted operation action on the resource",
        examples=["read"],
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description of permission scope",
        examples=["Grants access to retrieve user account profiles"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "perm_01HGBX1234567890ABCDEFGH",
                "resource": "users",
                "action": "read",
                "description": "Grants access to retrieve user account profiles",
            }
        }
    )


class RoleDTO(BaseModel):
    """Role detail data contract."""

    id: str = Field(
        ...,
        description="Unique role entity identifier",
        examples=["rol_01HGBX1234567890ABCDEFGH"],
    )
    name: str = Field(
        ...,
        description="Unique name identifier of the role",
        examples=["Analyst"],
    )
    description: str | None = Field(
        default=None,
        description="Summary description of role access scope",
        examples=["Business intelligence analyst with read-only view access"],
    )
    permissions: list[PermissionDTO] = Field(
        default_factory=list,
        description="List of permission objects assigned to this role",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rol_01HGBX1234567890ABCDEFGH",
                "name": "Analyst",
                "description": "Analyst role with read-only view access",
                "permissions": [
                    {
                        "id": "perm_01HGBX1234567890ABCDEFGH",
                        "resource": "users",
                        "action": "read",
                        "description": "Grants access to retrieve profiles",
                    }
                ],
            }
        }
    )


class CreateRoleDTO(BaseModel):
    """Data contract for creating a new role."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Unique name of the role to create",
        examples=["Data Engineer"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional description of the role responsibilities",
        examples=["Custom role for data pipeline metrics and schema management"],
    )
    permission_ids: list[str] = Field(
        default_factory=list,
        description="List of permission IDs to assign to the role",
        examples=[["perm_01HGBX1234567890ABCDEFGH"]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Data Engineer",
                "description": "Custom role for data pipeline metrics",
                "permission_ids": ["perm_01HGBX1234567890ABCDEFGH"],
            }
        }
    )


class UpdateRoleDTO(BaseModel):
    """Data contract for updating an existing role."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Updated name of the role",
        examples=["Senior Data Engineer"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated description of the role",
        examples=["Lead data engineer role with elevated dataset access"],
    )
    permission_ids: list[str] | None = Field(
        default=None,
        description="Updated list of permission IDs to assign to the role",
        examples=[["perm_01HGBX1234567890ABCDEFGH"]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Senior Data Engineer",
                "description": "Lead data engineer role with elevated dataset access",
                "permission_ids": ["perm_01HGBX1234567890ABCDEFGH"],
            }
        }
    )
