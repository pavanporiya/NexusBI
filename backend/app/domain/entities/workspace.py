"""Workspace domain entity.

Represents a multi-tenant workspace aggregate within an organization.
Enforces domain invariants.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.exceptions import DomainValidationError

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(slots=True)
class Workspace:
    """Represents a Workspace domain entity.

    Attributes
    ----------
    id : str
        UUID primary key.
    organization_id : str
        ID of parent Organization.
    name : str
        Workspace display name.
    slug : str
        URL-friendly unique identifier slug.
    description : str | None
        Optional workspace description.
    is_default : bool
        Whether this is the default workspace for the organization.
    is_active : bool
        Whether the workspace is active.
    created_at : datetime
        UTC creation timestamp.
    updated_at : datetime
        UTC last update timestamp.
    """

    id: str
    organization_id: str
    name: str
    slug: str
    description: str | None = None
    is_default: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate workspace domain invariants."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Workspace id must not be empty")
        if not self.organization_id or not self.organization_id.strip():
            raise DomainValidationError("Workspace organization_id must not be empty")
        if not self.name or not self.name.strip():
            raise DomainValidationError("Workspace name must not be empty")
        if not self.slug or not self.slug.strip():
            raise DomainValidationError("Workspace slug must not be empty")

        self.name = self.name.strip()
        self.organization_id = self.organization_id.strip()
        self.slug = self.slug.strip().lower()

        if not SLUG_REGEX.match(self.slug):
            raise DomainValidationError(
                "Workspace slug must contain only "
                "lowercase alphanumeric characters and hyphens"
            )

        if self.description is not None:
            self.description = self.description.strip() or None

    def update(
        self,
        name: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        is_default: bool | None = None,
        is_active: bool | None = None,
    ) -> None:
        """Update workspace attributes."""
        if name is not None:
            stripped_name = name.strip()
            if not stripped_name:
                raise DomainValidationError("Workspace name must not be empty")
            self.name = stripped_name

        if slug is not None:
            stripped_slug = slug.strip().lower()
            if not stripped_slug:
                raise DomainValidationError("Workspace slug must not be empty")
            if not SLUG_REGEX.match(stripped_slug):
                raise DomainValidationError(
                    "Workspace slug must contain only "
                    "lowercase alphanumeric characters and hyphens"
                )
            self.slug = stripped_slug

        if description is not None:
            self.description = description.strip() or None

        if is_default is not None:
            self.is_default = is_default

        if is_active is not None:
            self.is_active = is_active

        self.updated_at = datetime.now(UTC)
