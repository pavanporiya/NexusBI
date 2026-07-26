"""Delete Widget Use Case."""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.widget_repository import IWidgetRepository


class DeleteWidgetUseCase:
    """Orchestrates removing a widget entity."""

    def __init__(self, widget_repository: IWidgetRepository) -> None:
        self._widget_repo = widget_repository

    def execute(self, widget_id: str) -> bool:
        """Delete a Widget entity by ID.

        Parameters
        ----------
        widget_id : str
            Unique ID of widget to delete.

        Returns
        -------
        bool
            True if deleted successfully.
        """
        widget = self._widget_repo.get_by_id(widget_id)
        if widget is None:
            raise EntityNotFoundError("Widget", widget_id)

        return self._widget_repo.delete(widget_id)
