"""User entity ↔ ORM model mapper.

Provides bidirectional conversion between ``app.domain.entities.User``
and ``app.infrastructure.database.models.UserModel``. This mapper forms
the anti-corruption layer that prevents SQLAlchemy models from leaking
into the domain.
"""

from __future__ import annotations

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.database.models import (
    PermissionModel,
    RoleModel,
    UserModel,
)


class UserMapper:
    """Stateless mapper between User domain entities and UserModel ORM objects."""

    @staticmethod
    def to_domain(model: UserModel) -> User:
        """Convert a ``UserModel`` ORM instance to a ``User`` domain entity.

        Eagerly maps nested roles and permissions from the loaded
        ORM relationships.

        Parameters
        ----------
        model : UserModel
            The SQLAlchemy model to convert.

        Returns
        -------
        User
            A fully-hydrated domain entity.
        """
        roles = [
            Role(
                id=role_model.id,
                name=role_model.name,
                description=role_model.description,
                permissions=[
                    Permission(
                        id=perm_model.id,
                        resource=perm_model.resource,
                        action=perm_model.action,
                        description=perm_model.description,
                    )
                    for perm_model in role_model.permissions
                ],
            )
            for role_model in model.roles
        ]

        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_verified=model.is_verified,
            google_id=model.google_id,
            roles=roles,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: User) -> UserModel:
        """Convert a ``User`` domain entity to a new ``UserModel`` instance.

        Parameters
        ----------
        entity : User
            The domain entity to convert.

        Returns
        -------
        UserModel
            A new ORM model instance ready for persistence.

        Notes
        -----
        Role/permission relationships must be resolved separately by the
        repository (matching existing DB records) to maintain referential
        integrity.
        """
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            full_name=entity.full_name,
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            google_id=entity.google_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: UserModel, entity: User) -> UserModel:
        """Patch an existing ``UserModel`` with values from a domain entity.

        Used during upsert operations to update mutable fields without
        replacing the ORM instance (which would break SQLAlchemy identity map).

        Parameters
        ----------
        model : UserModel
            The existing ORM model to update in-place.
        entity : User
            The domain entity containing updated values.

        Returns
        -------
        UserModel
            The same model instance, mutated in-place.
        """
        model.email = str(entity.email)
        model.full_name = entity.full_name
        model.hashed_password = entity.hashed_password
        model.is_active = entity.is_active
        model.is_verified = entity.is_verified
        model.google_id = entity.google_id
        model.updated_at = entity.updated_at
        return model

    @staticmethod
    def _permission_to_model(entity: Permission) -> PermissionModel:
        """Convert a ``Permission`` domain entity to a ``PermissionModel``.

        Parameters
        ----------
        entity : Permission
            The domain permission entity.

        Returns
        -------
        PermissionModel
            A new ORM permission model instance.
        """
        return PermissionModel(
            id=entity.id,
            resource=entity.resource,
            action=entity.action,
            description=entity.description,
        )

    @staticmethod
    def _role_to_model(entity: Role) -> RoleModel:
        """Convert a ``Role`` domain entity to a ``RoleModel``.

        Parameters
        ----------
        entity : Role
            The domain role entity.

        Returns
        -------
        RoleModel
            A new ORM role model instance.
        """
        return RoleModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
        )
