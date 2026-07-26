"""Unit tests for Workspace domain entity."""

import pytest

from app.domain.entities.workspace import Workspace
from app.domain.exceptions import DomainValidationError


def test_workspace_creation_success() -> None:
    ws = Workspace(
        id="ws-1",
        organization_id="org-1",
        name="Sales Analytics",
        slug="sales-analytics",
        description="Workspace for sales team",
        is_default=True,
    )
    assert ws.id == "ws-1"
    assert ws.organization_id == "org-1"
    assert ws.name == "Sales Analytics"
    assert ws.slug == "sales-analytics"
    assert ws.description == "Workspace for sales team"
    assert ws.is_default is True
    assert ws.is_active is True


@pytest.mark.parametrize(
    ("invalid_id", "invalid_org_id", "invalid_name", "invalid_slug"),
    [
        ("", "org-1", "Sales", "sales"),
        ("ws-1", "", "Sales", "sales"),
        ("ws-1", "org-1", "", "sales"),
        ("ws-1", "org-1", "Sales", ""),
        ("ws-1", "org-1", "Sales", "invalid_slug!"),
    ],
)
def test_workspace_validation_failures(
    invalid_id: str, invalid_org_id: str, invalid_name: str, invalid_slug: str
) -> None:
    with pytest.raises(DomainValidationError):
        Workspace(
            id=invalid_id,
            organization_id=invalid_org_id,
            name=invalid_name,
            slug=invalid_slug,
        )


def test_workspace_update() -> None:
    ws = Workspace(
        id="ws-1",
        organization_id="org-1",
        name="Sales Analytics",
        slug="sales-analytics",
    )
    ws.update(name="RevOps", slug="revops", description="RevOps team", is_default=True)
    assert ws.name == "RevOps"
    assert ws.slug == "revops"
    assert ws.description == "RevOps team"
    assert ws.is_default is True
