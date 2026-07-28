"""Data transfer objects for connector management endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.connectors.types import ConnectorType


class ConnectorConfigDTO(BaseModel):
    """Connector configuration payload used for test and discovery APIs."""

    connector_type: ConnectorType = Field(
        ...,
        description="Connector technology type.",
        examples=["postgresql"],
    )
    id: str = Field(
        ..., description="Unique connector identifier.", examples=["connector-1"]
    )
    name: str = Field(
        ...,
        description="Human-friendly connector name.",
        examples=["Analytics Postgres"],
    )
    host: str | None = Field(
        default=None,
        description="Hostname or address of the data source.",
        examples=["localhost"],
    )
    port: int | None = Field(
        default=None,
        description="Port number used to connect.",
        examples=[5432],
    )
    database: str | None = Field(
        default=None,
        description="Database or catalog name.",
        examples=["analytics"],
    )
    username: str | None = Field(
        default=None,
        description="Authentication username.",
        examples=["db_user"],
    )
    password: str | None = Field(
        default=None,
        description="Authentication password.",
        examples=["secret"],
    )
    default_schema: str | None = Field(
        default=None,
        description="Default schema name for discovery operations.",
        examples=["public"],
        alias="schema",
        serialization_alias="schema",
    )
    warehouse: str | None = Field(
        default=None,
        description="Warehouse identifier for supported connector types.",
        examples=["analytics_wh"],
    )
    account: str | None = Field(
        default=None,
        description="Account identifier for supported connector types.",
        examples=["account123"],
    )
    ssl_enabled: bool = Field(
        default=False,
        description="Whether to use an encrypted connection.",
    )
    extra_options: dict[str, Any] = Field(
        default_factory=dict,
        description="Connector-specific option bag.",
        examples=[{"sslmode": "require"}],
    )

    model_config = ConfigDict(extra="forbid")


class ConnectorDiscoveryRequestDTO(ConnectorConfigDTO):
    """Connector discovery request payload with optional target table."""

    table_name: str | None = Field(
        default=None,
        description="Optional table name for column discovery.",
        examples=["users"],
    )


class ConnectorTestResponseDTO(BaseModel):
    """Response model for connector test operations."""

    success: bool = Field(
        ..., description="Indicates whether the connector test passed."
    )
    message: str = Field(
        ..., description="Human-readable connection test result message."
    )


class ConnectorColumnDTO(BaseModel):
    """Shape of column metadata returned by connector discovery."""

    name: str = Field(..., description="Column name.")
    type: str = Field(..., description="Column type.")
    nullable: bool = Field(..., description="Whether the column allows null values.")
    primary_key: bool = Field(
        ..., description="Whether the column is part of the table primary key."
    )


class ConnectorDiscoveryResponseDTO(BaseModel):
    """Response payload for connector metadata discovery operations."""

    schemas: list[str] = Field(
        ..., description="Discovered schemas available to the connector."
    )
    tables: list[str] = Field(
        ..., description="Discovered tables available to the connector."
    )
    columns: list[ConnectorColumnDTO] = Field(
        ..., description="Discovered column metadata for the requested table."
    )

    model_config = ConfigDict(frozen=True)
