"""SQLAlchemy implementation of the User repository.

Fulfills the ``IUserRepository`` Protocol contract defined in the domain layer.
SQLAlchemy models are never exposed outside this module — all public methods
accept and return domain entities exclusively.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities.user import User
from app.infrastructure.database.models import RoleModel, UserModel
from app.infrastructure.mappers.user_mapper import UserMapper


class SQLAlchemyUserRepository:
    """Concrete ``IUserRepository`` backed by SQLAlchemy/PostgreSQL.

    This class structurally satisfies the ``IUserRepository`` Protocol.
    It does **not** inherit from the Protocol — structural subtyping is
    sufficient for ``isinstance`` checks at runtime.

    Parameters
    ----------
    session : Session
        An active SQLAlchemy session (unit of work).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _user_query_options(self) -> list[Any]:
        """Return standard eager-loading options for user queries.

        Loads roles and their nested permissions in two additional
        SELECT statements (selectin) to avoid N+1 while keeping
        the primary query simple.
        """
        return [
            selectinload(UserModel.roles).selectinload(RoleModel.permissions),
        ]

    # ------------------------------------------------------------------
    # IUserRepository contract
    # ------------------------------------------------------------------

    def get_by_id(self, user_id: str) -> User | None:
        """Fetch a User by their unique system ID."""
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id)
            .options(*self._user_query_options())
        )
        model = self._session.execute(stmt).scalars().first()
        return UserMapper.to_domain(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        """Fetch a User by their unique email address."""
        normalized = email.strip().lower()
        stmt = (
            select(UserModel)
            .where(UserModel.email == normalized)
            .options(*self._user_query_options())
        )
        model = self._session.execute(stmt).scalars().first()
        return UserMapper.to_domain(model) if model else None

    def get_by_google_id(self, google_id: str) -> User | None:
        """Fetch a User by their linked Google account ID."""
        stmt = (
            select(UserModel)
            .where(UserModel.google_id == google_id)
            .options(*self._user_query_options())
        )
        model = self._session.execute(stmt).scalars().first()
        return UserMapper.to_domain(model) if model else None

    def save(self, user: User) -> User:
        """Persist a new User or update an existing one (upsert).

        For new users, creates the ORM model and resolves role
        relationships against existing DB records. For existing users,
        patches mutable fields and syncs role assignments.
        """
        existing = (
            self._session.execute(
                select(UserModel)
                .where(UserModel.id == user.id)
                .options(*self._user_query_options())
            )
            .scalars()
            .first()
        )

        if existing:
            UserMapper.update_model(existing, user)
            existing.roles = self._resolve_roles(user)
            model = existing
        else:
            model = UserMapper.to_model(user)
            model.roles = self._resolve_roles(user)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return UserMapper.to_domain(model)

    def delete(self, user_id: str) -> bool:
        """Permanently remove a User from persistence."""
        model = self._session.get(UserModel, user_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list_all(self, limit: int = 50, offset: int = 0) -> list[User]:
        """Fetch a paginated list of all users."""
        from sqlalchemy import select

        stmt = (
            select(UserModel)
            .order_by(UserModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        models = list(self._session.execute(stmt).scalars().all())
        return [UserMapper.to_domain(m) for m in models]

    def count_all(self) -> int:
        """Count total users."""
        from sqlalchemy import func, select

        count_q = select(func.count()).select_from(UserModel)
        return self._session.execute(count_q).scalar() or 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_roles(self, user: User) -> list[RoleModel]:
        """Resolve domain role entities to existing ORM role records.

        Roles are matched by ID against the database. Any role ID that
        does not exist in the database is silently skipped to prevent
        FK violations.
        """
        if not user.roles:
            return []

        role_ids = [r.id for r in user.roles]
        stmt = select(RoleModel).where(RoleModel.id.in_(role_ids))
        return list(self._session.execute(stmt).scalars().all())
