"""Membership entity ↔ ORM model mapper."""

from __future__ import annotations

from app.domain.entities.membership import Membership
from app.infrastructure.database.models import MembershipModel


class MembershipMapper:
    """Mapper between Membership entities and MembershipModel ORM objects."""

    @staticmethod
    def to_domain(model: MembershipModel) -> Membership:
        """Convert a MembershipModel ORM instance to a Membership domain entity."""
        return Membership(
            id=model.id,
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            role_id=model.role_id,
            joined_at=model.joined_at,
            is_active=model.is_active,
        )

    @staticmethod
    def to_model(entity: Membership) -> MembershipModel:
        """Convert a Membership domain entity to a new MembershipModel ORM instance."""
        return MembershipModel(
            id=entity.id,
            workspace_id=entity.workspace_id,
            user_id=entity.user_id,
            role_id=entity.role_id,
            joined_at=entity.joined_at,
            is_active=entity.is_active,
        )

    @staticmethod
    def update_model(model: MembershipModel, entity: Membership) -> None:
        """Update an existing MembershipModel from a Membership entity."""
        model.role_id = entity.role_id
        model.is_active = entity.is_active
