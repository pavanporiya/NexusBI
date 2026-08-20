"""Domain value object for structured chart specifications.

Provides Pydantic schema validation for chart specifications produced by the AI Agent
pipeline and Universal Chart Engine.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# Supported chart types for V1
SUPPORTED_V1_CHART_TYPES = {
    "line",
    "bar",
    "area",
    "pie",
    "table",
    "line_chart",
    "bar_chart",
    "area_chart",
    "pie_chart",
}


class ChartSpec(BaseModel):
    """Structured chart specification Pydantic model for V1 visualization."""

    type: str = Field(
        ...,
        description="Supported chart type: line, bar, area, pie, or table.",
    )
    title: str = Field(..., min_length=1, description="Chart title.")
    x_axis: str | None = Field(
        default=None, description="X-axis category/dimension column."
    )
    y_axis: str | list[str] | None = Field(
        default=None, description="Y-axis metric column or columns."
    )
    data: list[dict[str, Any]] = Field(
        default_factory=list, description="Authorized query result rows."
    )
    series: list[dict[str, Any]] | None = Field(
        default=None, description="Chart series data array."
    )
    labels: list[str] | None = Field(default=None, description="Category axis labels.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional visualization metadata."
    )

    @field_validator("type")
    @classmethod
    def validate_chart_type(cls, v: str) -> str:
        """Reject invalid chart types outside the supported V1 set."""
        if not isinstance(v, str):
            raise ValueError(f"Invalid chart type format: {v}")
        normalized = v.strip().lower()
        if normalized not in SUPPORTED_V1_CHART_TYPES:
            types_str = ", ".join(sorted(SUPPORTED_V1_CHART_TYPES))
            raise ValueError(
                f"Unsupported chart type '{v}'. Supported V1 types: {types_str}"
            )
        return normalized

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate non-empty title."""
        if not v or not v.strip():
            raise ValueError("Chart title must not be empty.")
        return v.strip()

    @model_validator(mode="after")
    def validate_pie_chart_rules(self) -> ChartSpec:
        """Validate that pie charts are only used when appropriate.

        Pie charts are appropriate when:
        1. Categorical dimension (x_axis) and metric column (y_axis) exist.
        2. Categorical items count is 10 or fewer.
        """
        if self.type in ("pie", "pie_chart"):
            if not self.x_axis or not self.y_axis:
                raise ValueError(
                    "Pie chart requires both x_axis (category) and y_axis (metric)."
                )
            if len(self.data) > 10:
                raise ValueError(
                    "Pie chart is not appropriate for >10 categories. "
                    "Use 'bar' or 'table' instead."
                )
        return self
