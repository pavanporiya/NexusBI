"""Connector type definitions for the Universal Data Connector Framework."""

from __future__ import annotations

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
