"""Authentication Data Transfer Objects (DTOs).

Defines serialization, validation, and type boundaries for application layer inputs and outputs.
Uses Pydantic v2.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class GoogleUserDTO(BaseModel):
    """Google OAuth profile information received from Google API."""

    google_id: str = Field(..., alias="sub")
    email: EmailStr
    email_verified: bool = False
    name: str | None = None
    picture: str | None = None


class UserDTO(BaseModel):
    """Normalized user detail data contract."""

    id: str
    email: EmailStr
    is_active: bool
    roles: list[str]
    permissions: list[str]
    created_at: datetime
    updated_at: datetime


class TokenDTO(BaseModel):
    """Access and refresh token response payload."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class LoginDTO(BaseModel):
    """Credentials required for standard password logins."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterDTO(BaseModel):
    """Input parameters needed to register a new local user."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenRefreshDTO(BaseModel):
    """Payload to request a token rotation."""

    refresh_token: str
