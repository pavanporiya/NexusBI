"""Connector type definitions for the Universal Data Connector Framework."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ConnectorType(StrEnum):
    """Supported database technologies for data connectors."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQLSERVER = "sqlserver"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    DUCKDB = "duckdb"


@dataclass(frozen=True, slots=True)
class ColumnMetadata:
    """Metadata representation for a database column."""

    name: str
    type: str
    nullable: bool
    primary_key: bool


@dataclass(frozen=True, slots=True)
class PrimaryKeyMetadata:
    """Metadata representation for a table primary key."""

    table_name: str
    schema: str | None
    constraint_name: str | None
    column_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ForeignKeyMetadata:
    """Metadata representation for a table foreign key."""

    name: str | None
    source_table: str
    source_schema: str | None
    constrained_columns: tuple[str, ...]
    referred_schema: str | None
    referred_table: str
    referred_columns: tuple[str, ...]
