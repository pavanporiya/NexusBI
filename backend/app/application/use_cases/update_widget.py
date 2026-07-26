"""Update Widget Use Case."""

from __future__ import annotations

from app.application.dto.widget_dto import UpdateWidgetDTO, WidgetDTO
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.repositories.widget_repository import IWidgetRepository


class UpdateWidgetUseCase:
    """Orchestrates updating editable widget fields."""

    def __init__(
        self,
        widget_repository: IWidgetRepository,
        dataset_repository: IDatasetRepository | None = None,
    ) -> None:
        self._widget_repo = widget_repository
        self._dataset_repo = dataset_repository

    def execute(self, widget_id: str, dto: UpdateWidgetDTO) -> WidgetDTO:
        """Update fields of an existing Widget entity.

        Parameters
        ----------
        widget_id : str
            Unique ID of widget to update.
        dto : UpdateWidgetDTO
            Update fields payload.

        Returns
        -------
        WidgetDTO
            The updated Widget DTO.
        """
        widget = self._widget_repo.get_by_id(widget_id)
        if widget is None:
            raise EntityNotFoundError("Widget", widget_id)

        if dto.dataset_id is not None and self._dataset_repo is not None:
            dataset = self._dataset_repo.get_by_id(dto.dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dto.dataset_id)

        if dto.title is not None:
            new_title = dto.title.strip()
            if new_title != widget.title:
                existing = self._widget_repo.get_by_dashboard_and_title(
                    widget.dashboard_id, new_title
                )
                if existing is not None and existing.id != widget.id:
                    raise DuplicateEntityError(
                        "Widget",
                        f"Dashboard '{widget.dashboard_id}' with title '{new_title}'",
                    )

        position_dict = dto.position.model_dump() if dto.position is not None else None
        size_dict = dto.size.model_dump() if dto.size is not None else None

        widget.update(
            title=dto.title,
            dataset_id=dto.dataset_id,
            widget_type=dto.widget_type,
            position=position_dict,
            size=size_dict,
            configuration=dto.configuration,
            refresh_interval=dto.refresh_interval,
            is_visible=dto.is_visible,
        )

        saved = self._widget_repo.save(widget)
        return WidgetDTO.from_domain(saved)
