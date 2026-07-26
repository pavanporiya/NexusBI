"""Report domain entity.

Represents an analytical report configuration, scheduling, and output format.
Enforces domain invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.enums import OutputFormat, ReportType
from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.schedule import Schedule


@dataclass(slots=True)
class Report:
    """Represents an analytical report aggregate entity.

    Attributes
    ----------
    id : str
        UUID primary key.
    name : str
        Report display name/title.
    dataset_id : str
        ID of the associated dataset (belongs to one Dataset).
    owner_id : str
        User ID of the report owner.
    report_type : ReportType | str
        Type of report (e.g., ReportType.TABULAR).
    output_format : OutputFormat | str
        Format for output/export (e.g., OutputFormat.JSON).
    description : str | None
        Optional summary or description of the report.
    schedule : Schedule | str | None
        Optional Schedule value object specification.
    is_active : bool
        Whether the report is active.
    created_at : datetime
        UTC creation timestamp.
    updated_at : datetime
        UTC modification timestamp.
    query : str
        Analytical query string.
    visualization_type : str
        Visualization chart type.
    config : dict[str, Any]
        Visualization configuration JSON.
    """

    id: str
    name: str
    dataset_id: str
    owner_id: str
    workspace_id: str = ""
    report_type: ReportType | str = ReportType.TABULAR
    output_format: OutputFormat | str = OutputFormat.JSON
    description: str | None = None
    schedule: Schedule | str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    query: str = ""
    visualization_type: str = "table"
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate report domain invariants."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Report id must not be empty")
        if not self.name or not self.name.strip():
            raise DomainValidationError("Report name must not be empty")
        if not self.owner_id or not self.owner_id.strip():
            raise DomainValidationError("Report owner_id must not be empty")
        if not self.dataset_id or not self.dataset_id.strip():
            raise DomainValidationError("Report dataset_id must not be empty")

        self.name = self.name.strip()
        self.owner_id = self.owner_id.strip()
        self.dataset_id = self.dataset_id.strip()

        if self.description is not None:
            self.description = self.description.strip() or None

        self._validate_report_type(self.report_type)
        self._validate_output_format(self.output_format)
        self._validate_schedule(self.schedule)

    def _validate_report_type(self, r_type: ReportType | str) -> None:
        if not r_type:
            raise DomainValidationError("Report report_type must not be empty")
        raw = (
            r_type.value
            if isinstance(r_type, ReportType)
            else str(r_type).strip().lower()
        )
        try:
            self.report_type = ReportType(raw)
        except ValueError as exc:
            valid_list = [e.value for e in ReportType]
            raise DomainValidationError(
                f"Invalid report_type '{raw}'. Must be one of: {valid_list}"
            ) from exc

    def _validate_output_format(self, o_format: OutputFormat | str) -> None:
        if not o_format:
            raise DomainValidationError("Report output_format must not be empty")
        raw = (
            o_format.value
            if isinstance(o_format, OutputFormat)
            else str(o_format).strip().lower()
        )
        try:
            self.output_format = OutputFormat(raw)
        except ValueError as exc:
            valid_list = [e.value for e in OutputFormat]
            raise DomainValidationError(
                f"Invalid output_format '{raw}'. Must be one of: {valid_list}"
            ) from exc

    def _validate_schedule(self, sched: Schedule | str | None) -> None:
        if sched is None:
            self.schedule = None
            return
        if isinstance(sched, Schedule):
            self.schedule = sched
        else:
            self.schedule = Schedule.create(sched)

    @property
    def schedule_str(self) -> str | None:
        """Return the string representation of schedule or None."""
        return str(self.schedule) if self.schedule is not None else None

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        dataset_id: str | None = None,
        report_type: ReportType | str | None = None,
        output_format: OutputFormat | str | None = None,
        schedule: Schedule | str | None = None,
        is_active: bool | None = None,
        query: str | None = None,
        visualization_type: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Update editable report attributes and touch updated_at."""
        if name is not None:
            stripped = name.strip()
            if not stripped:
                raise DomainValidationError("Report name must not be empty")
            self.name = stripped

        if description is not None:
            self.description = description.strip() if description else None

        if dataset_id is not None:
            stripped_ds = dataset_id.strip()
            if not stripped_ds:
                raise DomainValidationError("Report dataset_id must not be empty")
            self.dataset_id = stripped_ds

        if report_type is not None:
            self._validate_report_type(report_type)

        if output_format is not None:
            self._validate_output_format(output_format)

        if schedule is not None:
            self._validate_schedule(schedule)

        if is_active is not None:
            self.is_active = is_active

        if query is not None:
            self.query = query

        if visualization_type is not None:
            self.visualization_type = visualization_type

        if config is not None:
            self.config = config

        self.updated_at = datetime.now(UTC)
