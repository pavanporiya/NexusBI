"""Unit tests for Organization domain entity."""

import pytest

from app.domain.entities.organization import Organization
from app.domain.exceptions import DomainValidationError


def test_organization_creation_success() -> None:
    org = Organization(
        id="org-1",
        name="Acme Corp",
        slug="acme-corp",
    )
    assert org.id == "org-1"
    assert org.name == "Acme Corp"
    assert org.slug == "acme-corp"
    assert org.is_active is True


def test_organization_slug_lowercased() -> None:
    org = Organization(
        id="org-1",
        name="Acme Corp",
        slug="Acme-Corp",
    )
    assert org.slug == "acme-corp"


@pytest.mark.parametrize(
    ("invalid_id", "invalid_name", "invalid_slug"),
    [
        ("", "Acme Corp", "acme-corp"),
        ("org-1", "", "acme-corp"),
        ("org-1", "Acme Corp", ""),
        ("org-1", "Acme Corp", "invalid_slug!"),
        ("org-1", "Acme Corp", "invalid slug"),
    ],
)
def test_organization_validation_failures(
    invalid_id: str, invalid_name: str, invalid_slug: str
) -> None:
    with pytest.raises(DomainValidationError):
        Organization(
            id=invalid_id,
            name=invalid_name,
            slug=invalid_slug,
        )


def test_organization_update() -> None:
    org = Organization(
        id="org-1",
        name="Acme Corp",
        slug="acme-corp",
    )
    org.update(name="Acme Global", slug="acme-global", is_active=False)
    assert org.name == "Acme Global"
    assert org.slug == "acme-global"
    assert org.is_active is False
