"""Dataset domain entity.

Represents a data source definition, physical table reference, view, or SQL query spec
with metadata schema definitions. Enforces domain invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.enums import DatasetObjectType, DatasetSourceType
from app.domain.exceptions import DomainValidationError


@dataclass(slots=True)
class Dataset:
    """Represents a dataset aggregate domain entity.

    Attributes
    ----------
    id : str
        UUID primary key.
    name : str
        Dataset display name.
    source_type : DatasetSourceType | str
        Source adapter type (e.g. 'snowflake', 'postgres', 'csv', 'custom').
    query_or_table : str | None
        Legacy SQL query or physical table reference for backwards compatibility.
    owner_id : str
        User ID of the dataset owner.
    object_type : DatasetObjectType | str | None
        Object classification (TABLE, VIEW, QUERY).
    object_name : str | None
        Physical table or view name (required for TABLE and VIEW).
    sql_query : str | None
        Physical SQL query string (required for QUERY, prohibited for TABLE).
    connection_id : str | None
        Optional future-ready data connection reference ID.
    description : str | None
        Optional description of the dataset.
    schema_metadata : dict[str, Any]
        Field definitions, data types, and column metadata JSON.
    is_active : bool
        Whether the dataset is active for queries.
    created_at : datetime
        UTC timestamp of creation.
    updated_at : datetime
        UTC timestamp of last update.
    """

    id: str
    name: str
    source_type: DatasetSourceType | str
    workspace_id: str = ""
    query_or_table_val: str | None = field(default=None, repr=False)
    owner_id: str = ""
    object_type_val: DatasetObjectType | str | None = field(default=None, repr=False)
    object_name: str | None = None
    sql_query: str | None = None
    connection_id: str | None = None
    description: str | None = None
    schema_metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __init__(
        self,
        id: str,
        name: str,
        source_type: DatasetSourceType | str,
        workspace_id: str = "",
        query_or_table: str | None = None,
        owner_id: str = "",
        object_type: DatasetObjectType | str | None = None,
        object_name: str | None = None,
        sql_query: str | None = None,
        connection_id: str | None = None,
        description: str | None = None,
        schema_metadata: dict[str, Any] | None = None,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.source_type = source_type
        self.workspace_id = workspace_id.strip()
        self.query_or_table_val = query_or_table
        self.owner_id = owner_id
        self.object_type_val = object_type
        self.object_name = object_name
        self.sql_query = sql_query
        self.connection_id = connection_id
        self.description = description
        self.schema_metadata = dict(schema_metadata or {})
        self.is_active = is_active
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

        self._validate_and_normalize()

    def _validate_and_normalize(self) -> None:
        """Validate dataset domain invariants and resolve object parameters."""
        if not self.id or not self.id.strip():
            raise DomainValidationError("Dataset id must not be empty")
        if not self.name or not self.name.strip():
            raise DomainValidationError("Dataset name must not be empty")
        if not self.owner_id or not self.owner_id.strip():
            raise DomainValidationError("Dataset owner_id must not be empty")

        self.name = self.name.strip()
        self.owner_id = self.owner_id.strip()

        if self.connection_id is not None:
            self.connection_id = self.connection_id.strip() or None

        # Validate source_type Enum
        if not self.source_type or not str(self.source_type).strip():
            raise DomainValidationError("Dataset source_type must not be empty")

        st_raw = (
            self.source_type.value
            if isinstance(self.source_type, DatasetSourceType)
            else str(self.source_type).strip().lower()
        )
        try:
            self.source_type = DatasetSourceType(st_raw)
        except ValueError as exc:
            valid_sources = [e.value for e in DatasetSourceType]
            raise DomainValidationError(
                f"Invalid dataset source_type '{st_raw}'. "
                f"Must be one of: {valid_sources}"
            ) from exc

        # Resolve object_type, object_name, sql_query with backwards compatibility
        obj_type_input = self.object_type_val
        legacy_qt = self.query_or_table_val.strip() if self.query_or_table_val else None

        # Infer object_type if not explicitly provided
        if obj_type_input is None:
            if self.sql_query is not None and self.sql_query.strip():
                obj_type_input = DatasetObjectType.QUERY
            elif self.object_name is not None and self.object_name.strip():
                obj_type_input = DatasetObjectType.TABLE
            elif legacy_qt:
                upper_qt = legacy_qt.upper()
                if (
                    upper_qt.startswith("SELECT")
                    or upper_qt.startswith("WITH")
                    or " " in legacy_qt
                ):
                    obj_type_input = DatasetObjectType.QUERY
                    self.sql_query = legacy_qt
                else:
                    obj_type_input = DatasetObjectType.TABLE
                    self.object_name = legacy_qt
            else:
                raise DomainValidationError(
                    "Dataset requires object_type, object_name, "
                    "sql_query, or query_or_table"
                )

        # Validate object_type Enum
        ot_raw = (
            obj_type_input.value
            if isinstance(obj_type_input, DatasetObjectType)
            else str(obj_type_input).strip().lower()
        )
        try:
            resolved_obj_type = DatasetObjectType(ot_raw)
        except ValueError as exc:
            valid_types = [e.value for e in DatasetObjectType]
            raise DomainValidationError(
                f"Invalid dataset object_type '{ot_raw}'. Must be one of: {valid_types}"
            ) from exc

        self.object_type_val = resolved_obj_type

        # Enforce combination rules
        if resolved_obj_type == DatasetObjectType.TABLE:
            if not self.object_name or not self.object_name.strip():
                if legacy_qt and not (
                    legacy_qt.upper().startswith("SELECT")
                    or legacy_qt.upper().startswith("WITH")
                ):
                    self.object_name = legacy_qt
                else:
                    raise DomainValidationError(
                        "TABLE dataset requires non-empty object_name"
                    )
            self.object_name = self.object_name.strip()

            if self.sql_query is not None and self.sql_query.strip():
                raise DomainValidationError("TABLE dataset must not contain sql_query")
            self.sql_query = None

        elif resolved_obj_type == DatasetObjectType.VIEW:
            if not self.object_name or not self.object_name.strip():
                if legacy_qt:
                    self.object_name = legacy_qt
                else:
                    raise DomainValidationError(
                        "VIEW dataset requires non-empty object_name"
                    )
            self.object_name = self.object_name.strip()
            if self.sql_query is not None:
                self.sql_query = self.sql_query.strip() or None

        elif resolved_obj_type == DatasetObjectType.QUERY:
            if not self.sql_query or not self.sql_query.strip():
                if legacy_qt:
                    self.sql_query = legacy_qt
                else:
                    raise DomainValidationError(
                        "QUERY dataset requires non-empty sql_query"
                    )
            self.sql_query = self.sql_query.strip()
            if self.object_name is not None:
                self.object_name = self.object_name.strip() or None

        self.query_or_table_val = (
            self.sql_query
            if resolved_obj_type == DatasetObjectType.QUERY
            else (self.object_name or "")
        )

    @property
    def object_type(self) -> DatasetObjectType:
        """Return the strongly-typed DatasetObjectType."""
        assert isinstance(self.object_type_val, DatasetObjectType)
        return self.object_type_val

    @property
    def query_or_table(self) -> str:
        """Backward compatibility alias returning SQL query or physical object name."""
        if self.object_type == DatasetObjectType.QUERY:
            return self.sql_query or ""
        return self.object_name or ""

    @query_or_table.setter
    def query_or_table(self, value: str) -> None:
        """Backward compatibility setter."""
        val = value.strip()
        if self.object_type == DatasetObjectType.QUERY:
            self.sql_query = val
        else:
            self.object_name = val
        self.query_or_table_val = val

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        source_type: DatasetSourceType | str | None = None,
        query_or_table: str | None = None,
        object_type: DatasetObjectType | str | None = None,
        object_name: str | None = None,
        sql_query: str | None = None,
        connection_id: str | None = None,
        schema_metadata: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> None:
        """Update editable dataset attributes and touch updated_at."""
        if name is not None:
            stripped = name.strip()
            if not stripped:
                raise DomainValidationError("Dataset name must not be empty")
            self.name = stripped

        if description is not None:
            self.description = description

        if source_type is not None:
            self.source_type = source_type

        if object_type is not None:
            self.object_type_val = object_type

        if object_name is not None:
            self.object_name = object_name

        if sql_query is not None:
            self.sql_query = sql_query

        if connection_id is not None:
            self.connection_id = connection_id

        if query_or_table is not None:
            stripped_qt = query_or_table.strip()
            if not stripped_qt:
                raise DomainValidationError("Dataset query_or_table must not be empty")
            self.query_or_table_val = stripped_qt
            if self.object_type_val == DatasetObjectType.QUERY:
                self.sql_query = stripped_qt
            else:
                self.object_name = stripped_qt

        if schema_metadata is not None:
            self.schema_metadata = schema_metadata

        if is_active is not None:
            self.is_active = is_active

        self._validate_and_normalize()
        self.updated_at = datetime.now(UTC)
