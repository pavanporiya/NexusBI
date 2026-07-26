"""SQLAlchemy implementation of the Organization repository.

Fulfills the IOrganizationRepository Protocol contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.organization import Organization
from app.infrastructure.database.models import OrganizationModel
from app.infrastructure.mappers.organization_mapper import OrganizationMapper


class SQLAlchemyOrganizationRepository:
    """Concrete IOrganizationRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, organization_id: str) -> Organization | None:
        """Fetch an Organization by its unique ID."""
        stmt = select(OrganizationModel).where(OrganizationModel.id == organization_id)
        model = self._session.execute(stmt).scalars().first()
        return OrganizationMapper.to_domain(model) if model else None

    def get_by_slug(self, slug: str) -> Organization | None:
        """Fetch an Organization by its unique slug."""
        stmt = select(OrganizationModel).where(
            OrganizationModel.slug == slug.strip().lower()
        )
        model = self._session.execute(stmt).scalars().first()
        return OrganizationMapper.to_domain(model) if model else None

    def save(self, organization: Organization) -> Organization:
        """Persist a new Organization or update an existing one."""
        existing = self._session.get(OrganizationModel, organization.id)
        if existing:
            OrganizationMapper.update_model(existing, organization)
            model = existing
        else:
            model = OrganizationMapper.to_model(organization)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return OrganizationMapper.to_domain(model)

    def delete(self, organization_id: str) -> bool:
        """Permanently remove an Organization by ID."""
        model = self._session.get(OrganizationModel, organization_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list_all(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Organization], int]:
        """Fetch a paginated list of Organizations with total count."""
        stmt = select(OrganizationModel)
        count_stmt = select(func.count()).select_from(OrganizationModel)
        total = self._session.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(OrganizationModel.created_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        models = self._session.execute(stmt).scalars().all()
        return [OrganizationMapper.to_domain(m) for m in models], total
