"""Connector Management REST API endpoints (v1 namespace)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_connector_service
from app.application.dto.connector_dto import (
    ConnectorColumnDTO,
    ConnectorConfigDTO,
    ConnectorDiscoveryRequestDTO,
    ConnectorDiscoveryResponseDTO,
    ConnectorTestResponseDTO,
)
from app.application.services.connector_service import ConnectorService
from app.core.exceptions import ValidationError
from app.domain.connectors import ConnectorConfig
from app.domain.connectors.types import ColumnMetadata, ConnectorType

router = APIRouter(prefix="/connectors", tags=["Connector Management"])


def _build_connector_config(config_data: ConnectorConfigDTO) -> ConnectorConfig:
    """Normalize request payload into a ConnectorConfig domain model."""
    try:
        return ConnectorConfig(
            id=config_data.id or "connector-api-request",
            name=config_data.name or "Connector API Request",
            connector_type=config_data.connector_type,
            host=config_data.host,
            port=config_data.port,
            database=config_data.database,
            username=config_data.username,
            password=config_data.password,
            schema=config_data.default_schema,
            warehouse=config_data.warehouse,
            account=config_data.account,
            ssl_enabled=config_data.ssl_enabled,
            extra_options=getattr(config_data, "extra_options", {}) or {},
        )
    except ValueError as exc:
        raise ValidationError(
            message="Connector configuration is invalid",
            detail=str(exc),
        ) from exc


def _map_columns_to_dto(columns: list[ColumnMetadata]) -> list[ConnectorColumnDTO]:
    """Map domain column metadata values to ConnectorColumnDTO payload objects."""
    return [
        ConnectorColumnDTO(
            name=column.name,
            type=column.type,
            nullable=column.nullable,
            primary_key=column.primary_key,
        )
        for column in columns
    ]


@router.post(
    "/test",
    response_model=ConnectorTestResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Validate Connector Connectivity",
    operation_id="connector_test",
    response_description="Connector connectivity test result.",
    description=(
        "Tests the supplied connector configuration by verifying that a connection "
        "can be established to the target data source."
    ),
    responses={400: {"description": "Invalid request or connector configuration."}},
)
def test_connector(
    dto: ConnectorConfigDTO,
    connector_service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> ConnectorTestResponseDTO:
    """Test a database connector configuration."""
    success = connector_service.test_connection(_build_connector_config(dto))
    message = (
        "Connector connection succeeded." if success else "Connector connection failed."
    )
    return ConnectorTestResponseDTO(success=success, message=message)


@router.post(
    "/discover",
    response_model=ConnectorDiscoveryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Discover Connector Metadata",
    operation_id="connector_discover",
    response_description=(
        "Discovered schemas, tables, and optional column metadata from the connector."
    ),
    description=(
        "Discovers metadata from the connector. If a table_name is supplied, column "
        "details for that table are also returned."
    ),
    responses={400: {"description": "Invalid request or connector configuration."}},
)
def discover_connector(
    dto: ConnectorDiscoveryRequestDTO,
    connector_service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> ConnectorDiscoveryResponseDTO:
    """Discover metadata exposed by the configured data source."""
    result = connector_service.discover(
        _build_connector_config(dto),
        schema=dto.default_schema,
        table_name=dto.table_name,
    )
    return ConnectorDiscoveryResponseDTO(
        schemas=result.schemas,
        tables=result.tables,
        columns=_map_columns_to_dto(result.columns),
    )


@router.get(
    "/schemas",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List Connector Schemas",
    operation_id="connector_list_schemas",
    response_description="List of available connector schemas.",
    description=(
        "Returns a list of schemas exposed by the target connector configuration."
    ),
    responses={400: {"description": "Invalid connector configuration."}},
)
def list_schemas(
    connector_type: Annotated[
        ConnectorType, Query(..., description="Connector technology type.")
    ],
    host: Annotated[str | None, Query(description="Data source host.")] = None,
    port: Annotated[
        int | None, Query(ge=1, le=65535, description="Data source port.")
    ] = None,
    database: Annotated[
        str | None, Query(description="Database or catalog name.")
    ] = None,
    username: Annotated[
        str | None, Query(description="Authentication username.")
    ] = None,
    password: Annotated[
        str | None, Query(description="Authentication password.")
    ] = None,
    schema: Annotated[
        str | None, Query(description="Default schema name for discovery operations.")
    ] = None,
    warehouse: Annotated[
        str | None,
        Query(description="Warehouse identifier for supported connector types."),
    ] = None,
    account: Annotated[
        str | None,
        Query(description="Account identifier for supported connector types."),
    ] = None,
    ssl_enabled: Annotated[bool, Query(description="Whether to use SSL/TLS.")] = False,
    *,
    connector_service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> list[str]:
    """Return all schemas visible to the connector."""
    config = _build_connector_config(
        ConnectorConfigDTO(
            connector_type=connector_type,
            id="connector-api-request",
            name="Connector API Request",
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            schema=schema,
            warehouse=warehouse,
            account=account,
            ssl_enabled=ssl_enabled,
            extra_options={},
        )
    )
    return connector_service.list_schemas(config)


@router.get(
    "/tables",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List Connector Tables",
    operation_id="connector_list_tables",
    response_description="List of tables exposed by the connector.",
    description=(
        "Returns a list of tables exposed by the connector configuration, optionally "
        "limited to a single schema."
    ),
    responses={400: {"description": "Invalid connector configuration."}},
)
def list_tables(
    connector_type: Annotated[
        ConnectorType, Query(..., description="Connector technology type.")
    ],
    schema: Annotated[
        str | None, Query(description="Schema filter for the table list.")
    ] = None,
    host: Annotated[str | None, Query(description="Data source host.")] = None,
    port: Annotated[
        int | None, Query(ge=1, le=65535, description="Data source port.")
    ] = None,
    database: Annotated[
        str | None, Query(description="Database or catalog name.")
    ] = None,
    username: Annotated[
        str | None, Query(description="Authentication username.")
    ] = None,
    password: Annotated[
        str | None, Query(description="Authentication password.")
    ] = None,
    warehouse: Annotated[
        str | None,
        Query(description="Warehouse identifier for supported connector types."),
    ] = None,
    account: Annotated[
        str | None,
        Query(description="Account identifier for supported connector types."),
    ] = None,
    ssl_enabled: Annotated[bool, Query(description="Whether to use SSL/TLS.")] = False,
    *,
    connector_service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> list[str]:
    """Return tables visible to the connector.

    If schema is omitted, the connector will return tables for its default schema.
    """
    config = _build_connector_config(
        ConnectorConfigDTO(
            connector_type=connector_type,
            id="connector-api-request",
            name="Connector API Request",
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            schema=schema,
            warehouse=warehouse,
            account=account,
            ssl_enabled=ssl_enabled,
            extra_options={},
        )
    )
    return connector_service.list_tables(config, schema=schema)


@router.get(
    "/columns",
    response_model=list[ConnectorColumnDTO],
    status_code=status.HTTP_200_OK,
    summary="List Connector Columns",
    operation_id="connector_list_columns",
    response_description="Column metadata for a specified connector table.",
    description=(
        "Returns column metadata for a specified table in the connector configuration."
    ),
    responses={
        400: {"description": "Invalid connector configuration or missing table name."}
    },
)
def list_columns(
    connector_type: Annotated[
        ConnectorType, Query(..., description="Connector technology type.")
    ],
    table_name: Annotated[str, Query(..., description="Name of the target table.")],
    schema: Annotated[
        str | None, Query(description="Schema containing the target table.")
    ] = None,
    host: Annotated[str | None, Query(description="Data source host.")] = None,
    port: Annotated[
        int | None, Query(ge=1, le=65535, description="Data source port.")
    ] = None,
    database: Annotated[
        str | None, Query(description="Database or catalog name.")
    ] = None,
    username: Annotated[
        str | None, Query(description="Authentication username.")
    ] = None,
    password: Annotated[
        str | None, Query(description="Authentication password.")
    ] = None,
    warehouse: Annotated[
        str | None,
        Query(description="Warehouse identifier for supported connector types."),
    ] = None,
    account: Annotated[
        str | None,
        Query(description="Account identifier for supported connector types."),
    ] = None,
    ssl_enabled: Annotated[bool, Query(description="Whether to use SSL/TLS.")] = False,
    *,
    connector_service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> list[ConnectorColumnDTO]:
    """Return columns for a given table in the connector."""
    config = _build_connector_config(
        ConnectorConfigDTO(
            connector_type=connector_type,
            id="connector-api-request",
            name="Connector API Request",
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            schema=schema,
            warehouse=warehouse,
            account=account,
            ssl_enabled=ssl_enabled,
            extra_options={},
        )
    )
    columns = connector_service.list_columns(
        config, table_name=table_name, schema=schema
    )
    return [
        ConnectorColumnDTO(
            name=column.name,
            type=column.type,
            nullable=column.nullable,
            primary_key=column.primary_key,
        )
        for column in columns
    ]
