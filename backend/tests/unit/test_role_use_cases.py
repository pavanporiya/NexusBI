"""Unit tests for Role Management application use cases.

Verifies:
- GetRolesUseCase (successful list, empty list)
- GetRoleByIdUseCase (successful retrieval, role not found)
- CreateRoleUseCase (successful create, duplicate name, invalid permission)
- UpdateRoleUseCase (successful update, not found, duplicate name, invalid perm)
- DeleteRoleUseCase (successful delete, role not found, protected default role)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.dto.role_dto import CreateRoleDTO, UpdateRoleDTO
from app.application.use_cases import (
    CreateRoleUseCase,
    DeleteRoleUseCase,
    GetRoleByIdUseCase,
    GetRolesUseCase,
    UpdateRoleUseCase,
)
from app.core.exceptions import (
    BusinessRuleViolationError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.repositories.role_repository import IRoleRepository


@pytest.fixture
def mock_role_repo() -> MagicMock:
    return MagicMock(spec=IRoleRepository)


@pytest.fixture
def sample_role() -> Role:
    perm = Permission(
        id="perm-1",
        resource="roles",
        action="read",
        description="Read roles",
    )
    return Role(
        id="role-admin",
        name="Admin",
        description="Administrator role",
        permissions=[perm],
    )


class TestGetRolesUseCase:
    """Tests for GetRolesUseCase."""

    def test_get_roles_success(
        self, mock_role_repo: MagicMock, sample_role: Role
    ) -> None:
        """Retrieves list of roles successfully."""
        mock_role_repo.get_all.return_value = [sample_role]
        use_case = GetRolesUseCase(role_repository=mock_role_repo)

        results = use_case.execute()

        assert len(results) == 1
        assert results[0].id == "role-admin"
        assert results[0].name == "Admin"
        assert results[0].description == "Administrator role"
        assert len(results[0].permissions) == 1
        assert results[0].permissions[0].id == "perm-1"
        assert results[0].permissions[0].resource == "roles"
        assert results[0].permissions[0].action == "read"
        mock_role_repo.get_all.assert_called_once()

    def test_get_roles_empty(self, mock_role_repo: MagicMock) -> None:
        """Returns empty list when no roles exist."""
        mock_role_repo.get_all.return_value = []
        use_case = GetRolesUseCase(role_repository=mock_role_repo)

        results = use_case.execute()

        assert results == []
        mock_role_repo.get_all.assert_called_once()


class TestGetRoleByIdUseCase:
    """Tests for GetRoleByIdUseCase."""

    def test_get_role_by_id_success(
        self, mock_role_repo: MagicMock, sample_role: Role
    ) -> None:
        """Retrieves role by ID successfully."""
        mock_role_repo.get_by_id.return_value = sample_role
        use_case = GetRoleByIdUseCase(role_repository=mock_role_repo)

        result = use_case.execute("role-admin")

        assert result.id == "role-admin"
        assert result.name == "Admin"
        assert result.description == "Administrator role"
        assert len(result.permissions) == 1
        mock_role_repo.get_by_id.assert_called_once_with("role-admin")

    def test_get_role_by_id_not_found(self, mock_role_repo: MagicMock) -> None:
        """Raises EntityNotFoundError when role ID does not exist."""
        mock_role_repo.get_by_id.return_value = None
        use_case = GetRoleByIdUseCase(role_repository=mock_role_repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            use_case.execute("nonexistent-role")

        assert "Role" in exc_info.value.message
        assert exc_info.value.detail is not None
        assert "nonexistent-role" in exc_info.value.detail
        mock_role_repo.get_by_id.assert_called_once_with("nonexistent-role")


class TestCreateRoleUseCase:
    """Tests for CreateRoleUseCase."""

    def test_create_role_success(self, mock_role_repo: MagicMock) -> None:
        """Creates a new custom role with valid permissions."""
        mock_role_repo.get_by_name.return_value = None
        perm = Permission(id="perm-1", resource="roles", action="create")
        mock_role_repo.get_permissions_by_ids.return_value = [perm]
        mock_role_repo.save.side_effect = lambda role: role

        dto = CreateRoleDTO(
            name="Custom Editor",
            description="Custom editor role",
            permission_ids=["perm-1"],
        )
        use_case = CreateRoleUseCase(role_repository=mock_role_repo)
        result = use_case.execute(dto)

        assert result.name == "Custom Editor"
        assert result.description == "Custom editor role"
        assert len(result.permissions) == 1
        assert result.permissions[0].id == "perm-1"
        mock_role_repo.get_by_name.assert_called_once_with("Custom Editor")
        mock_role_repo.save.assert_called_once()

    def test_create_role_duplicate_name(self, mock_role_repo: MagicMock) -> None:
        """Raises DuplicateEntityError when role name already exists."""
        mock_role_repo.get_by_name.return_value = Role(id="existing-id", name="Admin")

        dto = CreateRoleDTO(name="Admin")
        use_case = CreateRoleUseCase(role_repository=mock_role_repo)

        with pytest.raises(DuplicateEntityError) as exc_info:
            use_case.execute(dto)

        assert "Role" in exc_info.value.message

    def test_create_role_invalid_permission(self, mock_role_repo: MagicMock) -> None:
        """Raises EntityNotFoundError when permission ID is missing."""
        mock_role_repo.get_by_name.return_value = None
        mock_role_repo.get_permissions_by_ids.return_value = []

        dto = CreateRoleDTO(name="New Role", permission_ids=["invalid-perm"])
        use_case = CreateRoleUseCase(role_repository=mock_role_repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            use_case.execute(dto)

        assert "Permission" in exc_info.value.message
        assert "invalid-perm" in (exc_info.value.detail or "")


class TestUpdateRoleUseCase:
    """Tests for UpdateRoleUseCase."""

    def test_update_role_success(
        self, mock_role_repo: MagicMock, sample_role: Role
    ) -> None:
        """Updates role fields successfully."""
        mock_role_repo.get_by_id.return_value = sample_role
        mock_role_repo.get_by_name.return_value = None
        perm = Permission(id="perm-2", resource="users", action="read")
        mock_role_repo.get_permissions_by_ids.return_value = [perm]
        mock_role_repo.save.side_effect = lambda role: role

        dto = UpdateRoleDTO(
            name="Updated Admin",
            description="Updated description",
            permission_ids=["perm-2"],
        )
        use_case = UpdateRoleUseCase(role_repository=mock_role_repo)
        result = use_case.execute("role-admin", dto)

        assert result.name == "Updated Admin"
        assert result.description == "Updated description"
        assert len(result.permissions) == 1
        assert result.permissions[0].id == "perm-2"

    def test_update_role_not_found(self, mock_role_repo: MagicMock) -> None:
        """Raises EntityNotFoundError when role to update does not exist."""
        mock_role_repo.get_by_id.return_value = None

        dto = UpdateRoleDTO(name="Updated Name")
        use_case = UpdateRoleUseCase(role_repository=mock_role_repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            use_case.execute("nonexistent-role", dto)

        assert "Role" in exc_info.value.message

    def test_update_role_duplicate_name(
        self, mock_role_repo: MagicMock, sample_role: Role
    ) -> None:
        """Raises DuplicateEntityError when updating to an existing role name."""
        mock_role_repo.get_by_id.return_value = sample_role
        mock_role_repo.get_by_name.return_value = Role(
            id="role-other", name="Super Admin"
        )

        dto = UpdateRoleDTO(name="Super Admin")
        use_case = UpdateRoleUseCase(role_repository=mock_role_repo)

        with pytest.raises(DuplicateEntityError) as exc_info:
            use_case.execute("role-admin", dto)

        assert "Role" in exc_info.value.message

    def test_update_role_invalid_permission(
        self, mock_role_repo: MagicMock, sample_role: Role
    ) -> None:
        """Raises EntityNotFoundError when assigned permission ID is invalid."""
        mock_role_repo.get_by_id.return_value = sample_role
        mock_role_repo.get_permissions_by_ids.return_value = []

        dto = UpdateRoleDTO(permission_ids=["nonexistent-perm"])
        use_case = UpdateRoleUseCase(role_repository=mock_role_repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            use_case.execute("role-admin", dto)

        assert "Permission" in exc_info.value.message


class TestDeleteRoleUseCase:
    """Tests for DeleteRoleUseCase."""

    def test_delete_role_success(self, mock_role_repo: MagicMock) -> None:
        """Deletes a custom role successfully."""
        custom_role = Role(id="custom-role-1", name="Custom Auditor")
        mock_role_repo.get_by_id.return_value = custom_role
        mock_role_repo.delete.return_value = True

        use_case = DeleteRoleUseCase(role_repository=mock_role_repo)
        use_case.execute("custom-role-1")

        mock_role_repo.get_by_id.assert_called_once_with("custom-role-1")
        mock_role_repo.delete.assert_called_once_with("custom-role-1")

    def test_delete_role_not_found(self, mock_role_repo: MagicMock) -> None:
        """Raises EntityNotFoundError when role to delete does not exist."""
        mock_role_repo.get_by_id.return_value = None

        use_case = DeleteRoleUseCase(role_repository=mock_role_repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            use_case.execute("nonexistent-role")

        assert "Role" in exc_info.value.message

    def test_delete_role_protected_default_role(
        self, mock_role_repo: MagicMock
    ) -> None:
        """Raises BusinessRuleViolationError when deleting default system role."""
        default_role = Role(id="role-admin", name="Admin")
        mock_role_repo.get_by_id.return_value = default_role

        use_case = DeleteRoleUseCase(role_repository=mock_role_repo)

        with pytest.raises(BusinessRuleViolationError) as exc_info:
            use_case.execute("role-admin")

        assert "Protected default role deletion" in exc_info.value.message
        assert "cannot be deleted" in (exc_info.value.detail or "")
