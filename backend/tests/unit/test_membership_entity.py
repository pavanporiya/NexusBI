"""Unit tests for Membership domain entity."""

import pytest

from app.domain.entities.membership import Membership
from app.domain.exceptions import DomainValidationError


def test_membership_creation_success() -> None:
    mem = Membership(
        id="mem-1",
        workspace_id="ws-1",
        user_id="usr-1",
        role_id="role-admin",
    )
    assert mem.id == "mem-1"
    assert mem.workspace_id == "ws-1"
    assert mem.user_id == "usr-1"
    assert mem.role_id == "role-admin"
    assert mem.is_active is True


@pytest.mark.parametrize(
    ("invalid_id", "invalid_ws_id", "invalid_user_id", "invalid_role_id"),
    [
        ("", "ws-1", "usr-1", "role-admin"),
        ("mem-1", "", "usr-1", "role-admin"),
        ("mem-1", "ws-1", "", "role-admin"),
        ("mem-1", "ws-1", "usr-1", ""),
    ],
)
def test_membership_validation_failures(
    invalid_id: str, invalid_ws_id: str, invalid_user_id: str, invalid_role_id: str
) -> None:
    with pytest.raises(DomainValidationError):
        Membership(
            id=invalid_id,
            workspace_id=invalid_ws_id,
            user_id=invalid_user_id,
            role_id=invalid_role_id,
        )


def test_membership_update_role() -> None:
    mem = Membership(
        id="mem-1",
        workspace_id="ws-1",
        user_id="usr-1",
        role_id="role-admin",
    )
    mem.update_role("role-viewer")
    assert mem.role_id == "role-viewer"

    with pytest.raises(DomainValidationError):
        mem.update_role("")
