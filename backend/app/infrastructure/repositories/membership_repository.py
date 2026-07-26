"""SQLAlchemy implementation of the Membership repository.

Fulfills the IMembershipRepository Protocol contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.membership import Membership
from app.infrastructure.database.models import MembershipModel
from app.infrastructure.mappers.membership_mapper import MembershipMapper


class SQLAlchemyMembershipRepository:
    """Concrete IMembershipRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, membership_id: str) -> Membership | None:
        """Fetch a Membership by its unique ID."""
        stmt = select(MembershipModel).where(MembershipModel.id == membership_id)
        model = self._session.execute(stmt).scalars().first()
        return MembershipMapper.to_domain(model) if model else None

    def get_by_workspace_and_user(
        self, workspace_id: str, user_id: str
    ) -> Membership | None:
        """Fetch a Membership by workspace ID and user ID."""
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id,
            MembershipModel.user_id == user_id,
        )
        model = self._session.execute(stmt).scalars().first()
        return MembershipMapper.to_domain(model) if model else None

    def save(self, membership: Membership) -> Membership:
        """Persist a new Membership or update an existing one."""
        existing = self._session.get(MembershipModel, membership.id)
        if existing:
            MembershipMapper.update_model(existing, membership)
            model = existing
        else:
            model = MembershipMapper.to_model(membership)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return MembershipMapper.to_domain(model)

    def delete(self, membership_id: str) -> bool:
        """Permanently remove a Membership by ID."""
        model = self._session.get(MembershipModel, membership_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list_by_workspace_id(
        self, workspace_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Membership], int]:
        """Fetch a paginated list of Memberships in a workspace with total count."""
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id
        )
        count_stmt = select(func.count()).where(
            MembershipModel.workspace_id == workspace_id
        )
        total = self._session.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(MembershipModel.joined_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        models = self._session.execute(stmt).scalars().all()
        return [MembershipMapper.to_domain(m) for m in models], total

    def list_by_user_id(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Membership], int]:
        """Fetch a paginated list of Memberships for a user across workspaces."""
        stmt = select(MembershipModel).where(MembershipModel.user_id == user_id)
        count_stmt = select(func.count()).where(MembershipModel.user_id == user_id)
        total = self._session.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(MembershipModel.joined_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        models = self._session.execute(stmt).scalars().all()
        return [MembershipMapper.to_domain(m) for m in models], total
