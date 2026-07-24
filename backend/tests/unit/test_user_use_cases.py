"""Unit tests for user application use cases.

Verifies business logic, validation, and error handling in:
- GetUserByIdUseCase
- UpdateUserProfileUseCase
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.application.dto.user_dto import UpdateUserDTO, UpdateUserProfileDTO
from app.application.use_cases.get_user_by_id import GetUserByIdUseCase
from app.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from app.core.exceptions import (
    BusinessRuleViolationError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository


@pytest.fixture
def mock_user_repo() -> MagicMock:
    return MagicMock(spec=IUserRepository)


@pytest.fixture
def active_user() -> User:
    now = datetime.now(UTC)
    return User(
        id="usr-100",
        email="john@example.com",
        full_name="John Doe",
        is_active=True,
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=1),
    )


@pytest.fixture
def inactive_user() -> User:
    now = datetime.now(UTC)
    return User(
        id="usr-200",
        email="inactive@example.com",
        full_name="Inactive User",
        is_active=False,
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=1),
    )


class TestGetUserByIdUseCase:
    """Unit tests for GetUserByIdUseCase."""

    def test_successful_retrieval(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = active_user
        use_case = GetUserByIdUseCase(user_repository=mock_user_repo)

        dto = use_case.execute("usr-100")

        assert dto.id == "usr-100"
        assert dto.email == "john@example.com"
        assert dto.full_name == "John Doe"
        assert dto.is_active is True
        mock_user_repo.get_by_id.assert_called_once_with("usr-100")

    def test_user_not_found(self, mock_user_repo: MagicMock) -> None:
        mock_user_repo.get_by_id.return_value = None
        use_case = GetUserByIdUseCase(user_repository=mock_user_repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            use_case.execute("usr-missing")

        assert exc_info.value.code == "NBI-4001"
        assert exc_info.value.status_code == 404
        assert "User" in exc_info.value.message

    def test_inactive_user(
        self, mock_user_repo: MagicMock, inactive_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = inactive_user
        use_case = GetUserByIdUseCase(user_repository=mock_user_repo)

        with pytest.raises(BusinessRuleViolationError) as exc_info:
            use_case.execute("usr-200")

        assert exc_info.value.code == "NBI-4003"
        assert exc_info.value.status_code == 422
        assert "inactive" in exc_info.value.message.lower()


class TestUpdateUserProfileUseCase:
    """Unit tests for UpdateUserProfileUseCase."""

    def test_successful_update(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = active_user
        mock_user_repo.save.side_effect = lambda user: user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        update_dto = UpdateUserProfileDTO(full_name="Jane Doe")
        result = use_case.execute("usr-100", update_dto)

        assert result.id == "usr-100"
        assert result.full_name == "Jane Doe"
        mock_user_repo.save.assert_called_once()

    def test_successful_email_update(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = active_user
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.save.side_effect = lambda user: user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        update_dto = UpdateUserProfileDTO(email="newjohn@example.com")
        result = use_case.execute("usr-100", update_dto)

        assert result.email == "newjohn@example.com"
        mock_user_repo.get_by_email.assert_called_once_with("newjohn@example.com")
        mock_user_repo.save.assert_called_once()

    def test_user_not_found(self, mock_user_repo: MagicMock) -> None:
        mock_user_repo.get_by_id.return_value = None
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            use_case.execute("usr-999", UpdateUserProfileDTO(full_name="Test"))

        assert exc_info.value.code == "NBI-4001"
        assert exc_info.value.status_code == 404

    def test_inactive_user(
        self, mock_user_repo: MagicMock, inactive_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = inactive_user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        with pytest.raises(BusinessRuleViolationError) as exc_info:
            use_case.execute("usr-200", UpdateUserProfileDTO(full_name="Test"))

        assert exc_info.value.code == "NBI-4003"
        assert exc_info.value.status_code == 422
        assert "inactive" in exc_info.value.message.lower()
        mock_user_repo.save.assert_not_called()

    def test_duplicate_email(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        other_user = User(id="usr-300", email="existing@example.com")
        mock_user_repo.get_by_id.return_value = active_user
        mock_user_repo.get_by_email.return_value = other_user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        with pytest.raises(DuplicateEntityError) as exc_info:
            use_case.execute(
                "usr-100", UpdateUserProfileDTO(email="existing@example.com")
            )

        assert exc_info.value.code == "NBI-4002"
        assert exc_info.value.status_code == 409
        mock_user_repo.save.assert_not_called()

    def test_same_email_no_duplicate_error(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = active_user
        mock_user_repo.save.side_effect = lambda user: user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        update_dto = UpdateUserProfileDTO(email="john@example.com")
        result = use_case.execute("usr-100", update_dto)

        assert result.email == "john@example.com"
        mock_user_repo.get_by_email.assert_not_called()

    def test_invalid_update_empty_name(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = active_user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        with pytest.raises(BusinessRuleViolationError) as exc_info:
            use_case.execute("usr-100", UpdateUserDTO(full_name="   "))

        assert exc_info.value.code == "NBI-4003"
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail is not None
        assert "empty" in exc_info.value.detail.lower()
        mock_user_repo.save.assert_not_called()

    def test_immutable_fields(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        mock_user_repo.get_by_id.return_value = active_user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        # Attempt to modify immutable id
        with pytest.raises(BusinessRuleViolationError) as exc_info_id:
            use_case.execute("usr-100", UpdateUserProfileDTO(id="usr-different"))

        assert exc_info_id.value.detail is not None
        assert "id" in exc_info_id.value.detail.lower()

        # Attempt to modify immutable created_at
        new_created_at = datetime.now(UTC)
        with pytest.raises(BusinessRuleViolationError) as exc_info_created:
            use_case.execute("usr-100", UpdateUserProfileDTO(created_at=new_created_at))

        assert exc_info_created.value.detail is not None
        assert "created_at" in exc_info_created.value.detail.lower()
        mock_user_repo.save.assert_not_called()

    def test_timestamp_update(
        self, mock_user_repo: MagicMock, active_user: User
    ) -> None:
        old_updated_at = active_user.updated_at
        mock_user_repo.get_by_id.return_value = active_user
        mock_user_repo.save.side_effect = lambda user: user
        use_case = UpdateUserProfileUseCase(user_repository=mock_user_repo)

        update_dto = UpdateUserProfileDTO(full_name="Updated Name")
        result = use_case.execute("usr-100", update_dto)

        assert result.updated_at > old_updated_at
        mock_user_repo.save.assert_called_once()
