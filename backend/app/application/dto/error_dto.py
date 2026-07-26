"""Structured Error Response Data Transfer Objects (DTOs) and OpenAPI helpers.

Defines Pydantic v2 schemas for the standardized NexusBI error response envelope,
error detail payloads, and reusable OpenAPI error response definitions.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FieldErrorDTO(BaseModel):
    """Field-level validation error detail."""

    field: str = Field(
        ...,
        description="Dot-separated path to the invalid request field",
        examples=["email"],
    )
    message: str = Field(
        ...,
        description="Human-readable validation failure message",
        examples=["value is not a valid email address"],
    )
    type: str = Field(
        ...,
        description="Validation error classification identifier",
        examples=["value_error.email"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "email",
                "message": "value is not a valid email address",
                "type": "value_error.email",
            }
        }
    )


class ErrorDetailDTO(BaseModel):
    """Structured payload containing error taxonomy code, message, and timestamp."""

    code: str = Field(
        ...,
        description="Unique NexusBI error taxonomy code (e.g. NBI-1001, NBI-1002)",
        examples=["NBI-1001"],
    )
    message: str = Field(
        ...,
        description="High-level error description summary",
        examples=["Request validation failed"],
    )
    detail: str = Field(
        ...,
        description="Detailed contextual diagnostic or remedy message",
        examples=["One or more request fields failed validation."],
    )
    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp when the error occurred",
        examples=["2026-07-24T22:28:37.000000Z"],
    )
    errors: list[FieldErrorDTO] | None = Field(
        default=None,
        description=(
            "Optional list of field-level validation errors for 422/400 responses"
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "NBI-1001",
                "message": "Request validation failed",
                "detail": "One or more request fields failed validation.",
                "timestamp": "2026-07-24T22:28:37.000000Z",
                "errors": [
                    {
                        "field": "email",
                        "message": "value is not a valid email address",
                        "type": "value_error.email",
                    }
                ],
            }
        }
    )


class ErrorResponseEnvelope(BaseModel):
    """Standardized top-level JSON response envelope for all HTTP error responses."""

    status: str = Field(
        default="error",
        description="Response status indicator (always 'error')",
        examples=["error"],
    )
    error: ErrorDetailDTO = Field(
        ...,
        description="Structured error payload detailing the failure",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "error",
                "error": {
                    "code": "NBI-1001",
                    "message": "Request validation failed",
                    "detail": "One or more request fields failed validation.",
                    "timestamp": "2026-07-24T22:28:37.000000Z",
                },
            }
        }
    )


# Reusable OpenAPI error responses dictionary mapping status codes to docs
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ErrorResponseEnvelope,
        "description": (
            "Bad Request — Invalid parameters, malformed payload, or bad format."
        ),
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-1001",
                        "message": "Request validation failed",
                        "detail": "Query parameter length exceeds maximum limit.",
                        "timestamp": "2026-07-24T22:28:37Z",
                    },
                }
            }
        },
    },
    401: {
        "model": ErrorResponseEnvelope,
        "description": "Unauthorized — Missing, invalid, or expired JWT bearer token.",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-1002",
                        "message": "Authentication failed",
                        "detail": (
                            "The provided access token has expired. Please refresh."
                        ),
                        "timestamp": "2026-07-24T22:28:37Z",
                    },
                }
            }
        },
    },
    403: {
        "model": ErrorResponseEnvelope,
        "description": (
            "Forbidden — Authenticated user lacks required permission or role."
        ),
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-1003",
                        "message": "Permission denied",
                        "detail": "Requires permission 'users:read'.",
                        "timestamp": "2026-07-24T22:28:37Z",
                    },
                }
            }
        },
    },
    404: {
        "model": ErrorResponseEnvelope,
        "description": "Not Found — Requested resource entity does not exist.",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-4001",
                        "message": "User not found",
                        "detail": "User with id 'usr_123' does not exist.",
                        "timestamp": "2026-07-24T22:28:37Z",
                    },
                }
            }
        },
    },
    409: {
        "model": ErrorResponseEnvelope,
        "description": "Conflict — Uniqueness constraint or resource state conflict.",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-4002",
                        "message": "User already exists",
                        "detail": (
                            "User with identifier 'user@example.com' already exists."
                        ),
                        "timestamp": "2026-07-24T22:28:37Z",
                    },
                }
            }
        },
    },
    422: {
        "model": ErrorResponseEnvelope,
        "description": (
            "Unprocessable Entity — Input validation error on field values."
        ),
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-1001",
                        "message": "Request validation failed",
                        "detail": "One or more request fields failed validation.",
                        "timestamp": "2026-07-24T22:28:37Z",
                        "errors": [
                            {
                                "field": "email",
                                "message": "value is not a valid email address",
                                "type": "value_error.email",
                            }
                        ],
                    },
                }
            }
        },
    },
    500: {
        "model": ErrorResponseEnvelope,
        "description": "Internal Server Error — Unexpected backend failure.",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-9999",
                        "message": "An unexpected server error occurred",
                        "detail": "An internal database error occurred.",
                        "timestamp": "2026-07-24T22:28:37Z",
                    },
                }
            }
        },
    },
    503: {
        "model": ErrorResponseEnvelope,
        "description": (
            "Service Unavailable — Critical system dependency unavailable."
        ),
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "NBI-3003",
                        "message": "Database connection failed",
                        "detail": "PostgreSQL database is currently unreachable.",
                        "timestamp": "2026-07-24T22:28:37Z",
                    },
                }
            }
        },
    },
}


def create_error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Return an OpenAPI responses dict filtered to specified error status codes."""
    return {
        code: ERROR_RESPONSES[code] for code in status_codes if code in ERROR_RESPONSES
    }
