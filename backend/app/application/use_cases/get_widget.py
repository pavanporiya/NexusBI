"""Get Widget Use Case."""

from __future__ import annotations

from app.application.dto.widget_dto import WidgetDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.widget_repository import IWidgetRepository


class GetWidgetUseCase:
    """Orchestrates fetching details of a widget by ID."""

    def __init__(self, widget_repository: IWidgetRepository) -> None:
        self._widget_repo = widget_repository

    def execute(self, widget_id: str) -> WidgetDTO:
        """Retrieve details of a single Widget by ID.

        Parameters
        ----------
        widget_id : str
            Unique ID of widget.

        Returns
        -------
        WidgetDTO
            Widget DTO details.
        """
        widget = self._widget_repo.get_by_id(widget_id)
        if widget is None:
            raise EntityNotFoundError("Widget", widget_id)

        return WidgetDTO.from_domain(widget)
