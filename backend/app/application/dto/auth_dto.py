"""Authentication Data Transfer Objects (DTOs).

Defines serialization, validation, and type boundaries for
application layer inputs and outputs.
Uses Pydantic v2.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GoogleUserDTO(BaseModel):
    """Google OAuth profile information received from Google API."""

    google_id: str = Field(
        ...,
        alias="sub",
        description="Google account unique subject identifier",
        examples=["109876543210987654321"],
    )
    email: EmailStr = Field(
        ...,
        description="Google account primary email address",
        examples=["user@gmail.com"],
    )
    email_verified: bool = Field(
        default=False,
        description="Whether email address is verified by Google",
        examples=[True],
    )
    name: str | None = Field(
        default=None,
        description="User display name from Google profile",
        examples=["Jane Doe"],
    )
    picture: str | None = Field(
        default=None,
        description="URL to user Google avatar image",
        examples=["https://lh3.googleusercontent.com/a/default-user"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "109876543210987654321",
                "email": "user@gmail.com",
                "email_verified": True,
                "name": "Jane Doe",
                "picture": "https://lh3.googleusercontent.com/a/default-user",
            }
        }
    )


class UserDTO(BaseModel):
    """Normalized user detail data contract."""

    id: str = Field(
        ...,
        description="Unique user entity identifier",
        examples=["usr_01HGBX1234567890ABCDEFGH"],
    )
    email: EmailStr = Field(
        ...,
        description="Primary email address of the user",
        examples=["user@example.com"],
    )
    full_name: str | None = Field(
        default=None,
        description="User's full display name",
        examples=["Jane Doe"],
    )
    is_active: bool = Field(
        ...,
        description="Indicates whether user account is active",
        examples=[True],
    )
    roles: list[str] = Field(
        ...,
        description="List of RBAC role names assigned to the user",
        examples=[["Analyst"]],
    )
    permissions: list[str] = Field(
        ...,
        description="List of permission action strings granted to the user",
        examples=[["users:read", "roles:read"]],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the user account was created",
        examples=["2026-01-15T08:30:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the user account was last updated",
        examples=["2026-07-24T12:00:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "usr_01HGBX1234567890ABCDEFGH",
                "email": "user@example.com",
                "full_name": "Jane Doe",
                "is_active": True,
                "roles": ["Analyst"],
                "permissions": ["users:read", "roles:read"],
                "created_at": "2026-01-15T08:30:00Z",
                "updated_at": "2026-07-24T12:00:00Z",
            }
        }
    )


class TokenDTO(BaseModel):
    """Access and refresh token response payload."""

    access_token: str = Field(
        ...,
        description="Cryptographically signed JWT access token",
        examples=["eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    refresh_token: str = Field(
        ...,
        description="Opaque refresh token used for session rotation",
        examples=["ref_01HGBX998877665544332211"],
    )
    token_type: str = Field(
        default="Bearer",
        description="HTTP authorization scheme type",
        examples=["Bearer"],
    )
    expires_in: int = Field(
        ...,
        description="Access token validity duration in seconds",
        examples=[3600],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.jwt_access_token",
                "refresh_token": "ref_01HGBX998877665544332211",
                "token_type": "Bearer",
                "expires_in": 3600,
            }
        }
    )


class LoginDTO(BaseModel):
    """Credentials required for standard password logins."""

    email: EmailStr = Field(
        ...,
        description="Registered user account email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Account password (minimum 8 characters)",
        examples=["SecureP@ssw0rd!"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecureP@ssw0rd!",
            }
        }
    )


class RegisterDTO(BaseModel):
    """Input parameters needed to register a new local user."""

    email: EmailStr = Field(
        ...,
        description="Primary email address for new user registration",
        examples=["newuser@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Account password (minimum 8 characters)",
        examples=["SecureP@ssw0rd!"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "SecureP@ssw0rd!",
            }
        }
    )


class TokenRefreshDTO(BaseModel):
    """Payload to request a token rotation."""

    refresh_token: str = Field(
        ...,
        description="Valid opaque refresh token to rotate",
        examples=["ref_01HGBX998877665544332211"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "ref_01HGBX998877665544332211",
            }
        }
    )


class LogoutResponseDTO(BaseModel):
    """Response payload returned upon successful session revocation."""

    message: str = Field(
        default="Successfully logged out",
        description="Session revocation status confirmation message",
        examples=["Successfully logged out"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Successfully logged out",
            }
        }
    )
