"""Resize Widget Use Case."""

from __future__ import annotations

from app.application.dto.widget_dto import ResizeWidgetDTO, WidgetDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.widget_repository import IWidgetRepository


class ResizeWidgetUseCase:
    """Orchestrates updating a widget's width and height grid dimensions."""

    def __init__(self, widget_repository: IWidgetRepository) -> None:
        self._widget_repo = widget_repository

    def execute(self, widget_id: str, dto: ResizeWidgetDTO) -> WidgetDTO:
        """Resize a widget to new grid dimensions (width, height).

        Parameters
        ----------
        widget_id : str
            Unique widget ID.
        dto : ResizeWidgetDTO
            Grid size payload (width, height).

        Returns
        -------
        WidgetDTO
            Updated Widget DTO.
        """
        widget = self._widget_repo.get_by_id(widget_id)
        if widget is None:
            raise EntityNotFoundError("Widget", widget_id)

        widget.resize(width=dto.width, height=dto.height)
        saved = self._widget_repo.save(widget)
        return WidgetDTO.from_domain(saved)
