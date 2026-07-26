"""Report entity ↔ ORM model mapper."""

from __future__ import annotations

from app.domain.entities.report import Report
from app.domain.enums import OutputFormat, ReportType
from app.domain.value_objects.schedule import Schedule
from app.infrastructure.database.models import ReportModel


class ReportMapper:
    """Stateless mapper between Report domain entities and ReportModel ORM objects."""

    @staticmethod
    def to_domain(model: ReportModel) -> Report:
        """Convert a ReportModel ORM instance to a Report domain entity."""
        return Report(
            id=model.id,
            name=model.name,
            dataset_id=model.dataset_id,
            owner_id=model.owner_id,
            workspace_id=model.workspace_id or "",
            report_type=ReportType(model.report_type)
            if model.report_type in [e.value for e in ReportType]
            else model.report_type,
            output_format=OutputFormat(model.output_format)
            if model.output_format in [e.value for e in OutputFormat]
            else model.output_format,
            description=model.description,
            schedule=Schedule.create(model.schedule),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            query=model.query or "",
            visualization_type=model.visualization_type or "table",
            config=dict(model.config or {}),
        )

    @staticmethod
    def to_model(entity: Report) -> ReportModel:
        """Convert a Report domain entity to a new ReportModel ORM instance."""
        r_type = (
            entity.report_type.value
            if hasattr(entity.report_type, "value")
            else str(entity.report_type)
        )
        o_format = (
            entity.output_format.value
            if hasattr(entity.output_format, "value")
            else str(entity.output_format)
        )
        return ReportModel(
            id=entity.id,
            name=entity.name,
            dataset_id=entity.dataset_id,
            owner_id=entity.owner_id,
            workspace_id=entity.workspace_id or None,
            report_type=r_type,
            output_format=o_format,
            description=entity.description,
            schedule=entity.schedule_str,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            query=entity.query,
            visualization_type=entity.visualization_type,
            config=dict(entity.config or {}),
        )

    @staticmethod
    def update_model(model: ReportModel, entity: Report) -> None:
        """Update an existing ReportModel ORM instance from a Report domain entity."""
        r_type = (
            entity.report_type.value
            if hasattr(entity.report_type, "value")
            else str(entity.report_type)
        )
        o_format = (
            entity.output_format.value
            if hasattr(entity.output_format, "value")
            else str(entity.output_format)
        )
        model.name = entity.name
        model.dataset_id = entity.dataset_id
        model.workspace_id = entity.workspace_id or None
        model.report_type = r_type
        model.output_format = o_format
        model.description = entity.description
        model.schedule = entity.schedule_str
        model.is_active = entity.is_active
        model.query = entity.query
        model.visualization_type = entity.visualization_type
        model.config = dict(entity.config or {})
        model.updated_at = entity.updated_at
