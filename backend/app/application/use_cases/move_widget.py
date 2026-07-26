"""Move Widget Use Case."""

from __future__ import annotations

from app.application.dto.widget_dto import MoveWidgetDTO, WidgetDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.widget_repository import IWidgetRepository


class MoveWidgetUseCase:
    """Orchestrates updating a widget's grid row and column position."""

    def __init__(self, widget_repository: IWidgetRepository) -> None:
        self._widget_repo = widget_repository

    def execute(self, widget_id: str, dto: MoveWidgetDTO) -> WidgetDTO:
        """Move a widget to a new grid position (row, column).

        Parameters
        ----------
        widget_id : str
            Unique widget ID.
        dto : MoveWidgetDTO
            Grid position payload (row, column).

        Returns
        -------
        WidgetDTO
            Updated Widget DTO.
        """
        widget = self._widget_repo.get_by_id(widget_id)
        if widget is None:
            raise EntityNotFoundError("Widget", widget_id)

        widget.move(row=dto.row, column=dto.column)
        saved = self._widget_repo.save(widget)
        return WidgetDTO.from_domain(saved)
