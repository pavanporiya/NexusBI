"""Get user by ID use case.

Orchestrates loading a user profile by unique user identifier.
"""

from __future__ import annotations

from app.application.use_cases.get_user_by_id import GetUserByIdUseCase

# Alias for backward compatibility
GetUserUseCase = GetUserByIdUseCase

__all__ = ["GetUserByIdUseCase", "GetUserUseCase"]
