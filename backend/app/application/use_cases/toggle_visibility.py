"""Toggle Widget Visibility Use Case."""

from __future__ import annotations

from app.application.dto.widget_dto import ToggleVisibilityDTO, WidgetDTO
from app.core.exceptions import EntityNotFoundError
from app.domain.repositories.widget_repository import IWidgetRepository


class ToggleVisibilityUseCase:
    """Orchestrates toggling or setting a widget's visibility status."""

    def __init__(self, widget_repository: IWidgetRepository) -> None:
        self._widget_repo = widget_repository

    def execute(
        self, widget_id: str, dto: ToggleVisibilityDTO | None = None
    ) -> WidgetDTO:
        """Toggle or explicitly set a widget's visibility.

        Parameters
        ----------
        widget_id : str
            Unique widget ID.
        dto : ToggleVisibilityDTO | None
            Optional payload carrying explicit is_visible boolean flag.

        Returns
        -------
        WidgetDTO
            Updated Widget DTO.
        """
        widget = self._widget_repo.get_by_id(widget_id)
        if widget is None:
            raise EntityNotFoundError("Widget", widget_id)

        target_visible = dto.is_visible if dto is not None else None
        widget.toggle_visibility(visible=target_visible)
        saved = self._widget_repo.save(widget)
        return WidgetDTO.from_domain(saved)
