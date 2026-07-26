"""Organization domain entity.

Represents an enterprise organization aggregate in the multi-tenant BI platform.
Enforces domain invariants.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.exceptions import DomainValidationError

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(slots=True)
class Organization:
    """Represents an Organization domain entity.

    Attributes
    ----------
    id : str
        UUID primary key.
    name : str
        Organization display name.
    slug : str
        URL-friendly unique identifier slug.
    is_active : bool
        Whether the organization is active.
    created_at : datetime
        UTC creation timestamp.
    updated_at : datetime
        UTC last update timestamp.
    """

    id: str
    name: str
    slug: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate organization domain invariants."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Organization id must not be empty")
        if not self.name or not self.name.strip():
            raise DomainValidationError("Organization name must not be empty")
        if not self.slug or not self.slug.strip():
            raise DomainValidationError("Organization slug must not be empty")

        self.name = self.name.strip()
        self.slug = self.slug.strip().lower()

        if not SLUG_REGEX.match(self.slug):
            raise DomainValidationError(
                "Organization slug must contain only "
                "lowercase alphanumeric characters and hyphens"
            )

    def update(
        self,
        name: str | None = None,
        slug: str | None = None,
        is_active: bool | None = None,
    ) -> None:
        """Update organization attributes."""
        if name is not None:
            stripped_name = name.strip()
            if not stripped_name:
                raise DomainValidationError("Organization name must not be empty")
            self.name = stripped_name

        if slug is not None:
            stripped_slug = slug.strip().lower()
            if not stripped_slug:
                raise DomainValidationError("Organization slug must not be empty")
            if not SLUG_REGEX.match(stripped_slug):
                raise DomainValidationError(
                    "Organization slug must contain only "
                    "lowercase alphanumeric characters and hyphens"
                )
            self.slug = stripped_slug

        if is_active is not None:
            self.is_active = is_active

        self.updated_at = datetime.now(UTC)
