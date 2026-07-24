"""SQLAlchemy implementation of the Role repository.

Fulfills the ``IRoleRepository`` Protocol contract defined in the domain layer.
SQLAlchemy models are never exposed outside this module — all public methods
accept and return domain entities exclusively.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.infrastructure.database.models import PermissionModel, RoleModel


class SQLAlchemyRoleRepository:
    """Concrete ``IRoleRepository`` backed by SQLAlchemy/PostgreSQL.

    Parameters
    ----------
    session : Session
        An active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def _role_query_options(self) -> list[Any]:
        """Return standard eager-loading options for role queries."""
        return [selectinload(RoleModel.permissions)]

    def get_all(self) -> list[Role]:
        """Fetch all roles."""
        stmt = select(RoleModel).options(*self._role_query_options())
        models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def get_by_id(self, role_id: str) -> Role | None:
        """Fetch a Role by its unique system ID."""
        stmt = (
            select(RoleModel)
            .where(RoleModel.id == role_id)
            .options(*self._role_query_options())
        )
        model = self._session.execute(stmt).scalars().first()
        return self._to_domain(model) if model else None

    def get_by_name(self, name: str) -> Role | None:
        """Fetch a Role by its name (case-insensitive)."""
        normalized = name.strip().lower()
        stmt = (
            select(RoleModel)
            .where(func.lower(RoleModel.name) == normalized)
            .options(*self._role_query_options())
        )
        model = self._session.execute(stmt).scalars().first()
        return self._to_domain(model) if model else None

    def get_permissions_by_ids(self, permission_ids: list[str]) -> list[Permission]:
        """Fetch permission entities matching given permission IDs or names."""
        if not permission_ids:
            return []

        conditions: list[Any] = [PermissionModel.id.in_(permission_ids)]
        qnames = [p for p in permission_ids if ":" in p]
        for qname in qnames:
            parts = qname.split(":", 1)
            conditions.append(
                and_(
                    PermissionModel.resource == parts[0],
                    PermissionModel.action == parts[1],
                )
            )

        stmt = select(PermissionModel).where(or_(*conditions))
        models = self._session.execute(stmt).scalars().all()
        return [
            Permission(
                id=pm.id,
                resource=pm.resource,
                action=pm.action,
                description=pm.description,
            )
            for pm in models
        ]

    def save(self, role: Role) -> Role:
        """Persist a new Role or update an existing one (upsert)."""
        existing = (
            self._session.execute(
                select(RoleModel)
                .where(RoleModel.id == role.id)
                .options(*self._role_query_options())
            )
            .scalars()
            .first()
        )

        perm_ids = [p.id for p in role.permissions]
        perm_models: list[PermissionModel] = []
        if perm_ids:
            perm_stmt = select(PermissionModel).where(PermissionModel.id.in_(perm_ids))
            perm_models = list(self._session.execute(perm_stmt).scalars().all())

        if existing:
            existing.name = role.name
            existing.description = role.description
            existing.permissions = perm_models
            model = existing
        else:
            model = RoleModel(
                id=role.id,
                name=role.name,
                description=role.description,
                permissions=perm_models,
            )
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def delete(self, role_id: str) -> bool:
        """Permanently remove a Role from persistence."""
        model = self._session.get(RoleModel, role_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    @staticmethod
    def _to_domain(model: RoleModel) -> Role:
        """Convert a RoleModel ORM instance to a Role domain entity."""
        permissions = [
            Permission(
                id=pm.id,
                resource=pm.resource,
                action=pm.action,
                description=pm.description,
            )
            for pm in model.permissions
        ]
        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            permissions=permissions,
        )
