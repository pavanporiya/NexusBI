"""Update user profile use case.

Orchestrates updating user profile details.
"""

from __future__ import annotations

from app.application.use_cases.update_user_profile import UpdateUserProfileUseCase

# Alias for backward compatibility
UpdateUserUseCase = UpdateUserProfileUseCase

__all__ = ["UpdateUserProfileUseCase", "UpdateUserUseCase"]
