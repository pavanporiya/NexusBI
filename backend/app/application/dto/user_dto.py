"""User management Data Transfer Objects (DTOs).

Defines input payloads for user management REST API operations.
Uses Pydantic v2.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UpdateUserProfileDTO(BaseModel):
    """Input payload for updating user profile details."""

    full_name: str | None = Field(default=None)
    email: EmailStr | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    id: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
    google_id: str | None = Field(default=None)


# Backward compatibility alias
UpdateUserDTO = UpdateUserProfileDTO
