"""Production-ready PostgreSQL connector implementation."""

from __future__ import annotations

import logging
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from app.domain.connectors import (
    AuthenticationFailedError,
    ConnectionFailedError,
    ConnectorConfig,
    DatabaseConnector,
    MetadataDiscoveryError,
    QueryExecutionError,
)
from app.domain.connectors.types import (
    ColumnMetadata,
    ForeignKeyMetadata,
    PrimaryKeyMetadata,
)

logger = logging.getLogger(__name__)


class PostgresConnector(DatabaseConnector):
    """SQLAlchemy-based PostgreSQL connector implementation.

    Features:
    - Connection pooling with configurable pool size and overflow
    - Transaction support with explicit begin/commit/rollback
    - Query execution with parameterized queries
    - Database metadata discovery (schemas, tables, views, columns)
    - Automatic connection lifecycle management
    """

    def __init__(self, config: ConnectorConfig) -> None:
        """Initialize the PostgreSQL connector with configuration.

        Args:
            config: ConnectorConfig instance with connection parameters

        Raises:
            ValueError: If required PostgreSQL parameters are missing
        """
        self._config = config
        self._engine: Engine | None = None
        self._connection: Connection | None = None
        self._transaction_active = False

        # Validate required PostgreSQL configuration
        if not self._config.host:
            raise ValueError("host is required for PostgreSQL connections")
        if not self._config.database:
            raise ValueError("database is required for PostgreSQL connections")

    def _build_connection_string(self) -> str:
        """Build a PostgreSQL connection string from config.

        Returns:
            PostgreSQL connection string in psycopg2 URL format

        Raises:
            AuthenticationFailedError: If credentials are missing/invalid
        """
        if not self._config.username:
            raise AuthenticationFailedError("username is required")
        if not self._config.password:
            raise AuthenticationFailedError("password is required")

        port = self._config.port or 5432
        user = self._config.username
        password = self._config.password
        host = self._config.host
        db = self._config.database

        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

    def _create_engine(self) -> Engine:
        """Create a SQLAlchemy engine with connection pooling.

        Returns:
            Configured SQLAlchemy Engine instance

        Raises:
            ConnectionFailedError: If engine creation fails
        """
        try:
            connection_string = self._build_connection_string()

            # Extract pool configuration from extra_options or use defaults
            def _opt_int(key: str, default: int) -> int:
                val: object = self._config.extra_options.get(key, default)
                if isinstance(val, (int, str)) and not isinstance(val, bool):
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        return default
                return default

            pool_size = _opt_int("pool_size", 10)
            max_overflow = _opt_int("max_overflow", 20)
            pool_timeout = _opt_int("pool_timeout", 30)
            pool_recycle = _opt_int("pool_recycle", 3600)

            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                pool_pre_ping=True,  # Verify connections before using
                echo=bool(self._config.extra_options.get("echo", False)),
                connect_args={
                    "connect_timeout": _opt_int("connect_timeout", 10),
                    "sslmode": "require" if self._config.ssl_enabled else "prefer",
                },
            )

            logger.info(
                f"Created PostgreSQL engine for {self._config.host}:"
                f"{self._config.port or 5432}/{self._config.database}"
            )
            return engine

        except SQLAlchemyError as e:
            logger.error(f"Failed to create PostgreSQL engine: {e}")
            raise ConnectionFailedError(
                f"Failed to create database engine: {str(e)}"
            ) from e

    def connect(self) -> None:
        """Open a connection to the configured PostgreSQL database.

        Raises:
            ConnectionFailedError: If connection cannot be established
        """
        if self._connection is not None:
            logger.warning("Connection already established")
            return

        try:
            if self._engine is None:
                self._engine = self._create_engine()

            self._connection = self._engine.connect()
            logger.info(f"Connected to PostgreSQL database {self._config.database}")

        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionFailedError(
                f"Failed to connect to {self._config.host}: {str(e)}"
            ) from e

    def disconnect(self) -> None:
        """Close the active connection and clean up resources.

        Ensures transaction is rolled back if active before closing.
        """
        try:
            if self._transaction_active:
                logger.info("Rolling back active transaction during disconnect")
                self.rollback()

            if self._connection is not None:
                self._connection.close()
                self._connection = None
                logger.info("Disconnected from PostgreSQL database")

            if self._engine is not None:
                self._engine.dispose()
                logger.info("Disposed of connection pool")

        except SQLAlchemyError as e:
            logger.error(f"Error during disconnect: {e}")

    def test_connection(self) -> bool:
        """Test whether the configured data source can be reached.

        Returns:
            True if connection is successful, False otherwise
        """
        temp_connection = None
        try:
            if self._engine is None:
                self._engine = self._create_engine()

            temp_connection = self._engine.connect()
            temp_connection.execute(text("SELECT 1"))
            logger.info(f"Successfully tested connection to {self._config.database}")
            return True

        except SQLAlchemyError as e:
            logger.warning(f"Connection test failed for {self._config.database}: {e}")
            return False

        finally:
            if temp_connection is not None:
                temp_connection.close()

    @contextmanager
    def _ensure_connection(self) -> Generator[Connection]:
        """Context manager to ensure an active connection exists.

        Yields:
            Active SQLAlchemy Connection instance

        Raises:
            ConnectionFailedError: If no connection is available
        """
        if self._connection is None:
            raise ConnectionFailedError(
                "Not connected. Call connect() before executing queries."
            )
        yield self._connection

    def execute(
        self, query: str, parameters: Mapping[str, object] | None = None
    ) -> Sequence[Mapping[str, object]]:
        """Execute a SQL query and return result rows.

        Args:
            query: SQL query string (supports parameterized queries)
            parameters: Optional parameter mapping for parameterized queries

        Returns:
            Sequence of result rows as dictionaries

        Raises:
            ConnectionFailedError: If not connected
            QueryExecutionError: If query execution fails
        """
        try:
            with self._ensure_connection() as connection:
                stmt = text(query)

                # Use parameters if provided
                if parameters:
                    result = connection.execute(stmt, parameters)
                else:
                    result = connection.execute(stmt)

                # Convert rows to list of dictionaries
                rows = [dict(row._mapping) for row in result]
                logger.debug(f"Executed query, returned {len(rows)} rows")
                return rows

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}")
            raise QueryExecutionError(f"Failed to execute query: {str(e)}") from e

    def begin_transaction(self) -> None:
        """Begin a database transaction.

        Raises:
            ConnectionFailedError: If not connected
        """
        try:
            with self._ensure_connection() as connection:
                if not connection.in_transaction():
                    connection.begin()
                self._transaction_active = True
                logger.debug("Transaction started")

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to begin transaction: {e}")
            raise QueryExecutionError(f"Failed to begin transaction: {str(e)}") from e

    def commit(self) -> None:
        """Commit the active transaction.

        Raises:
            ConnectionFailedError: If not connected
            QueryExecutionError: If commit fails
        """
        try:
            with self._ensure_connection() as connection:
                if connection.in_transaction():
                    connection.commit()
                self._transaction_active = False
                logger.debug("Transaction committed")

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to commit transaction: {e}")
            self._transaction_active = False
            raise QueryExecutionError(f"Failed to commit transaction: {str(e)}") from e

    def rollback(self) -> None:
        """Rollback the active transaction.

        Raises:
            ConnectionFailedError: If not connected
            QueryExecutionError: If rollback fails
        """
        try:
            with self._ensure_connection() as connection:
                if connection.in_transaction():
                    connection.rollback()
                self._transaction_active = False
                logger.debug("Transaction rolled back")

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to rollback transaction: {e}")
            self._transaction_active = False
            raise QueryExecutionError(
                f"Failed to rollback transaction: {str(e)}"
            ) from e

    def list_schemas(self) -> Sequence[str]:
        """List all schemas in the PostgreSQL database.

        Returns:
            Sequence of schema names (excluding system schemas)

        Raises:
            ConnectionFailedError: If not connected
            MetadataDiscoveryError: If schema discovery fails
        """
        try:
            with self._ensure_connection() as connection:
                inspector = inspect(connection)
                schemas = inspector.get_schema_names()

                # Filter out system schemas
                system_schemas = {"information_schema", "pg_catalog", "pg_toast"}
                user_schemas = [s for s in schemas if s not in system_schemas]

                logger.debug(f"Found {len(user_schemas)} user schemas")
                return user_schemas

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to discover schemas: {e}")
            raise MetadataDiscoveryError(f"Failed to discover schemas: {str(e)}") from e

    def list_tables(self, schema: str | None = None) -> Sequence[str]:
        """List all tables in the database or a specific schema.

        Args:
            schema: Optional schema name (uses default if not provided)

        Returns:
            Sequence of table names

        Raises:
            ConnectionFailedError: If not connected
            MetadataDiscoveryError: If table discovery fails
        """
        try:
            with self._ensure_connection() as connection:
                inspector = inspect(connection)

                # Use provided schema or default (public)
                target_schema = schema or "public"

                tables = inspector.get_table_names(schema=target_schema)
                logger.debug(f"Found {len(tables)} tables in schema {target_schema}")
                return tables

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to discover tables in schema {schema}: {e}")
            raise MetadataDiscoveryError(f"Failed to discover tables: {str(e)}") from e

    def list_views(self, schema: str | None = None) -> Sequence[str]:
        """List all views in the database or a specific schema.

        Args:
            schema: Optional schema name (uses default if not provided)

        Returns:
            Sequence of view names

        Raises:
            ConnectionFailedError: If not connected
            MetadataDiscoveryError: If view discovery fails
        """
        try:
            with self._ensure_connection() as connection:
                inspector = inspect(connection)

                # Use provided schema or default (public)
                target_schema = schema or "public"

                views = inspector.get_view_names(schema=target_schema)
                logger.debug(f"Found {len(views)} views in schema {target_schema}")
                return views

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to discover views in schema {schema}: {e}")
            raise MetadataDiscoveryError(f"Failed to discover views: {str(e)}") from e

    def list_columns(
        self, table_name: str, schema: str | None = None
    ) -> Sequence[ColumnMetadata]:
        """List column metadata for a table or view.

        Args:
            table_name: Name of the table/view
            schema: Optional schema name (uses default if not provided)

        Returns:
            Sequence of ColumnMetadata objects describing the target table/view.

        Raises:
            ConnectionFailedError: If not connected
            MetadataDiscoveryError: If column discovery fails
        """
        try:
            with self._ensure_connection() as connection:
                inspector = inspect(connection)

                # Use provided schema or default (public)
                target_schema = schema or "public"

                columns = inspector.get_columns(table_name, schema=target_schema)

                result: list[ColumnMetadata] = [
                    ColumnMetadata(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=bool(col["nullable"]),
                        primary_key=bool(col.get("primary_key", False)),
                    )
                    for col in columns
                ]

                logger.debug(
                    f"Found {len(result)} columns for {target_schema}.{table_name}"
                )
                return result

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to discover columns for {schema}.{table_name}: {e}")
            raise MetadataDiscoveryError(f"Failed to discover columns: {str(e)}") from e

    def list_primary_keys(
        self, table_name: str, schema: str | None = None
    ) -> Sequence[PrimaryKeyMetadata]:
        """List primary keys for a table."""
        try:
            with self._ensure_connection() as connection:
                inspector = inspect(connection)
                target_schema = schema or "public"

                constraint = inspector.get_pk_constraint(
                    table_name, schema=target_schema
                )
                column_names = tuple(constraint.get("constrained_columns") or [])

                if not column_names:
                    logger.debug(
                        f"No primary key found for {target_schema}.{table_name}"
                    )
                    return []

                primary_key_metadata = PrimaryKeyMetadata(
                    table_name=table_name,
                    schema=target_schema,
                    constraint_name=constraint.get("name"),
                    column_names=column_names,
                )

                logger.debug(
                    f"Found primary key on {target_schema}.{table_name}: {column_names}"
                )
                return [primary_key_metadata]

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to discover primary keys for {schema}.{table_name}: {e}"
            )
            raise MetadataDiscoveryError(
                f"Failed to discover primary keys: {str(e)}"
            ) from e

    def list_foreign_keys(
        self, table_name: str, schema: str | None = None
    ) -> Sequence[ForeignKeyMetadata]:
        """List foreign keys for a table."""
        try:
            with self._ensure_connection() as connection:
                inspector = inspect(connection)
                target_schema = schema or "public"

                foreign_keys = inspector.get_foreign_keys(
                    table_name, schema=target_schema
                )
                result: list[ForeignKeyMetadata] = [
                    ForeignKeyMetadata(
                        name=fk.get("name"),
                        source_table=table_name,
                        source_schema=target_schema,
                        constrained_columns=tuple(fk.get("constrained_columns") or []),
                        referred_schema=fk.get("referred_schema"),
                        referred_table=str(fk["referred_table"]),
                        referred_columns=tuple(fk.get("referred_columns") or []),
                    )
                    for fk in foreign_keys
                ]

                logger.debug(
                    f"Found {len(result)} foreign keys for {target_schema}.{table_name}"
                )
                return result

        except ConnectionFailedError:
            raise
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to discover foreign keys for {schema}.{table_name}: {e}"
            )
            raise MetadataDiscoveryError(
                f"Failed to discover foreign keys: {str(e)}"
            ) from e

    def __del__(self) -> None:
        """Ensure resources are cleaned up on object deletion."""
        try:
            self.disconnect()
        except Exception as e:
            logger.warning(f"Error during connector cleanup: {e}")
