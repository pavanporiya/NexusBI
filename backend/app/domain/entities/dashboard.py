"""Dashboard domain entity.

Represents an interactive dashboard configuration referencing a dataset.
Enforces domain invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.dashboard_layout import DashboardLayout


@dataclass(slots=True)
class Dashboard:
    """Represents a BI dashboard entity.

    Attributes
    ----------
    id : str
        UUID primary key.
    name : str
        Dashboard display title/name.
    owner_id : str
        User ID of the dashboard owner.
    dataset_id : str
        ID of the dataset referenced by this dashboard.
    description : str | None
        Optional text describing the dashboard's purpose.
    layout : DashboardLayout
        Strongly typed DashboardLayout value object configuration.
    is_public : bool
        Whether the dashboard is publicly visible within the workspace.
    is_active : bool
        Whether the dashboard is active.
    created_at : datetime
        UTC timestamp of creation.
    updated_at : datetime
        UTC timestamp of last modification.
    """

    id: str
    name: str
    owner_id: str
    dataset_id: str
    workspace_id: str = ""
    description: str | None = None
    layout_val: DashboardLayout = field(default_factory=DashboardLayout, repr=False)
    is_public: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __init__(
        self,
        id: str,
        name: str,
        owner_id: str,
        dataset_id: str,
        workspace_id: str = "",
        description: str | None = None,
        layout: DashboardLayout | dict[str, Any] | None = None,
        layout_json: dict[str, Any] | DashboardLayout | None = None,
        layout_config: dict[str, Any] | DashboardLayout | None = None,
        is_public: bool = False,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.dataset_id = dataset_id
        self.workspace_id = workspace_id.strip()
        self.description = description
        self.is_public = is_public
        self.is_active = is_active
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

        raw_layout = layout or layout_json or layout_config or {}
        if isinstance(raw_layout, DashboardLayout):
            self.layout_val = raw_layout
        elif isinstance(raw_layout, dict):
            self.layout_val = DashboardLayout.from_dict(raw_layout)
        else:
            self.layout_val = DashboardLayout()

        self.__post_init__()

    def __post_init__(self) -> None:
        """Validate dashboard domain invariants."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Dashboard id must not be empty")
        if not self.name or not self.name.strip():
            raise DomainValidationError("Dashboard name must not be empty")
        if not self.owner_id or not self.owner_id.strip():
            raise DomainValidationError("Dashboard owner_id must not be empty")
        if not self.dataset_id or not self.dataset_id.strip():
            raise DomainValidationError("Dashboard dataset_id must not be empty")

        self.name = self.name.strip()
        self.owner_id = self.owner_id.strip()
        self.dataset_id = self.dataset_id.strip()

        if not isinstance(self.layout_val, DashboardLayout):
            raise DomainValidationError(
                "Dashboard layout must be a DashboardLayout instance"
            )

    @property
    def layout(self) -> DashboardLayout:
        """Expose strongly typed DashboardLayout object."""
        return self.layout_val

    @layout.setter
    def layout(self, value: DashboardLayout | dict[str, Any]) -> None:
        if isinstance(value, DashboardLayout):
            self.layout_val = value
        elif isinstance(value, dict):
            self.layout_val = DashboardLayout.from_dict(value)
        else:
            raise DomainValidationError("Invalid layout assignment")

    @property
    def layout_json(self) -> dict[str, Any]:
        """Backward compatibility alias for layout_json dict."""
        return self.layout_val.to_dict()

    @layout_json.setter
    def layout_json(self, value: dict[str, Any] | DashboardLayout) -> None:
        """Backward compatibility setter for layout_json."""
        self.layout = value

    @property
    def layout_config(self) -> dict[str, Any]:
        """Backward compatibility alias for layout_config dict."""
        return self.layout_json

    @layout_config.setter
    def layout_config(self, value: dict[str, Any] | DashboardLayout) -> None:
        """Backward compatibility setter for layout_config."""
        self.layout_json = value

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        dataset_id: str | None = None,
        layout: DashboardLayout | dict[str, Any] | None = None,
        layout_json: dict[str, Any] | DashboardLayout | None = None,
        layout_config: dict[str, Any] | DashboardLayout | None = None,
        is_public: bool | None = None,
        is_active: bool | None = None,
    ) -> None:
        """Update editable dashboard attributes and refresh updated_at timestamp."""
        if name is not None:
            stripped = name.strip()
            if not stripped:
                raise DomainValidationError("Dashboard name must not be empty")
            self.name = stripped

        if description is not None:
            self.description = description

        if dataset_id is not None:
            stripped_ds = dataset_id.strip()
            if not stripped_ds:
                raise DomainValidationError("Dashboard dataset_id must not be empty")
            self.dataset_id = stripped_ds

        target_layout = layout or layout_json or layout_config
        if target_layout is not None:
            self.layout = target_layout

        if is_public is not None:
            self.is_public = is_public

        if is_active is not None:
            self.is_active = is_active

        self.__post_init__()
        self.updated_at = datetime.now(UTC)
