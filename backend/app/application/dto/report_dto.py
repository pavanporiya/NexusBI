"""Report Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.entities.report import Report


class ReportDTO(BaseModel):
    """Data transfer object representing a Report entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(description="Unique Report identifier")
    name: str = Field(description="Report display name")
    dataset_id: str = Field(description="Associated Dataset identifier")
    owner_id: str = Field(description="Owner user identifier")
    report_type: str = Field(
        description="Type of report (e.g. tabular, chart, summary, pivot, custom)"
    )
    output_format: str = Field(
        description="Output export format (e.g. json, csv, pdf, excel, html)"
    )
    description: str | None = Field(default=None, description="Optional description")
    schedule: str | None = Field(
        default=None, description="Optional cron schedule spec"
    )
    is_active: bool = Field(default=True, description="Active status flag")
    created_at: datetime = Field(description="UTC timestamp of creation")
    updated_at: datetime = Field(description="UTC timestamp of last update")
    query: str = Field(default="", description="Analytical query string")
    visualization_type: str = Field(
        default="table", description="Visualization chart type"
    )
    config: dict[str, Any] = Field(
        default_factory=dict, description="Visualization configuration JSON"
    )

    @classmethod
    def from_domain(cls, entity: Report) -> ReportDTO:
        """Construct ReportDTO from a Report domain entity."""
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
        return cls(
            id=entity.id,
            name=entity.name,
            dataset_id=entity.dataset_id,
            owner_id=entity.owner_id,
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


class CreateReportDTO(BaseModel):
    """Data transfer object for creating a new Report."""

    name: str = Field(min_length=1, max_length=256, description="Report display name")
    dataset_id: str = Field(
        min_length=1, max_length=36, description="Associated Dataset ID"
    )
    report_type: str = Field(
        default="tabular", min_length=1, max_length=64, description="Report type"
    )
    output_format: str = Field(
        default="json", min_length=1, max_length=64, description="Output format"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    schedule: str | None = Field(
        default=None, max_length=128, description="Optional cron schedule spec"
    )
    is_active: bool = Field(default=True, description="Active status flag")
    query: str | None = Field(default="", description="Analytical query string")
    visualization_type: str | None = Field(
        default="table", description="Visualization chart type"
    )
    config: dict[str, Any] | None = Field(
        default_factory=dict, description="Visualization configuration JSON"
    )


class UpdateReportDTO(BaseModel):
    """Data transfer object for updating an existing Report."""

    name: str | None = Field(
        default=None, min_length=1, max_length=256, description="Updated name"
    )
    dataset_id: str | None = Field(
        default=None, min_length=1, max_length=36, description="Updated dataset ID"
    )
    report_type: str | None = Field(
        default=None, min_length=1, max_length=64, description="Updated report type"
    )
    output_format: str | None = Field(
        default=None, min_length=1, max_length=64, description="Updated output format"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Optional description"
    )
    schedule: str | None = Field(
        default=None, max_length=128, description="Updated cron schedule spec"
    )
    is_active: bool | None = Field(
        default=None, description="Optional active status flag"
    )
    query: str | None = Field(default=None, description="Updated query string")
    visualization_type: str | None = Field(
        default=None, description="Updated visualization chart type"
    )
    config: dict[str, Any] | None = Field(
        default=None, description="Updated visualization configuration JSON"
    )
