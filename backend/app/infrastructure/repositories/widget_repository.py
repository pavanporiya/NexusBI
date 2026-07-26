"""SQLAlchemy implementation of the Widget repository.

Fulfills the IWidgetRepository Protocol contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.widget import Widget
from app.infrastructure.database.models import WidgetModel
from app.infrastructure.mappers.widget_mapper import WidgetMapper


class SQLAlchemyWidgetRepository:
    """Concrete IWidgetRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, widget_id: str) -> Widget | None:
        """Fetch a Widget by its unique ID."""
        stmt = select(WidgetModel).where(WidgetModel.id == widget_id)
        model = self._session.execute(stmt).scalars().first()
        return WidgetMapper.to_domain(model) if model else None

    def list_by_dashboard_id(self, dashboard_id: str) -> list[Widget]:
        """Fetch all widgets contained inside a dashboard, ordered by grid position."""

        stmt = (
            select(WidgetModel)
            .where(WidgetModel.dashboard_id == dashboard_id)
            .order_by(WidgetModel.row.asc(), WidgetModel.column.asc())
        )
        models = self._session.execute(stmt).scalars().all()
        return [WidgetMapper.to_domain(m) for m in models]

    def get_by_dashboard_and_title(
        self, dashboard_id: str, title: str
    ) -> Widget | None:
        """Fetch a widget by dashboard ID and title (used for duplicate validation)."""
        stmt = select(WidgetModel).where(
            WidgetModel.dashboard_id == dashboard_id,
            WidgetModel.title == title,
        )
        model = self._session.execute(stmt).scalars().first()
        return WidgetMapper.to_domain(model) if model else None

    def save(self, widget: Widget) -> Widget:
        """Persist a new Widget or update an existing one."""
        existing = self._session.get(WidgetModel, widget.id)
        if existing:
            WidgetMapper.update_model(existing, widget)
            model = existing
        else:
            model = WidgetMapper.to_model(widget)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return WidgetMapper.to_domain(model)

    def delete(self, widget_id: str) -> bool:
        """Permanently remove a Widget by ID."""
        model = self._session.get(WidgetModel, widget_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True
