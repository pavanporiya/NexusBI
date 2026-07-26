"""User management Data Transfer Objects (DTOs).

Defines input payloads for user management REST API operations.
Uses Pydantic v2.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UpdateUserProfileDTO(BaseModel):
    """Input payload for updating user profile details."""

    full_name: str | None = Field(
        default=None,
        description="Updated full display name for the user",
        examples=["Jane Smith"],
    )
    email: EmailStr | None = Field(
        default=None,
        description="Updated email address for the user account",
        examples=["jane.smith@example.com"],
    )
    is_active: bool | None = Field(
        default=None,
        description="Account status flag (true to enable, false to disable)",
        examples=[True],
    )
    id: str | None = Field(
        default=None,
        description="User ID field (ignored on update processing)",
        examples=["usr_01HGBX1234567890ABCDEFGH"],
    )
    created_at: datetime | None = Field(
        default=None,
        description="Creation timestamp (ignored on update processing)",
        examples=["2026-01-15T08:30:00Z"],
    )
    google_id: str | None = Field(
        default=None,
        description="Google subject identifier (ignored on update processing)",
        examples=["109876543210987654321"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Jane Smith",
                "email": "jane.smith@example.com",
                "is_active": True,
            }
        }
    )


# Backward compatibility alias
UpdateUserDTO = UpdateUserProfileDTO
