"""Membership Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.entities.membership import Membership


class MembershipDTO(BaseModel):
    """Data transfer object representing a Membership domain entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(description="Unique Membership identifier")
    workspace_id: str = Field(description="Workspace identifier")
    user_id: str = Field(description="User identifier")
    role_id: str = Field(description="Assigned Role identifier")
    joined_at: datetime = Field(description="UTC timestamp of joining")
    is_active: bool = Field(default=True, description="Active status flag")

    @classmethod
    def from_domain(cls, entity: Membership) -> MembershipDTO:
        """Construct MembershipDTO from Membership domain entity."""
        return cls(
            id=entity.id,
            workspace_id=entity.workspace_id,
            user_id=entity.user_id,
            role_id=entity.role_id,
            joined_at=entity.joined_at,
            is_active=entity.is_active,
        )


class AddMemberDTO(BaseModel):
    """Data transfer object for adding a member to a workspace."""

    user_id: str = Field(
        min_length=1, max_length=64, description="User ID to add as member"
    )
    role_id: str = Field(
        min_length=1, max_length=64, description="Role ID to assign to member"
    )


class UpdateMemberRoleDTO(BaseModel):
    """Data transfer object for updating a member's assigned role."""

    role_id: str = Field(
        min_length=1, max_length=64, description="New Role ID for member"
    )
