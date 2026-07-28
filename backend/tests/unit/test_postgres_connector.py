"""Unit tests for PostgreSQL connector implementation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.domain.connectors import (
    AuthenticationFailedError,
    ConnectionFailedError,
    ConnectorConfig,
    ConnectorType,
    QueryExecutionError,
    UnsupportedConnectorError,
)
from app.domain.connectors.types import (
    ColumnMetadata,
    ForeignKeyMetadata,
    PrimaryKeyMetadata,
)
from app.infrastructure.connectors import ConnectorRegistry, PostgresConnector


class TestPostgresConnectorInitialization:
    """Test PostgreSQL connector initialization and validation."""

    def test_criar_connector_with_valid_config(self) -> None:
        """PostgreSQL connector initializes with valid configuration."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        assert connector._config == config
        assert connector._engine is None
        assert connector._connection is None

    def test_reject_connector_without_host(self) -> None:
        """PostgreSQL connector requires host parameter."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            database="testdb",
            username="user",
            password="pass",
        )

        with pytest.raises(ValueError, match="host is required"):
            PostgresConnector(config)

    def test_reject_connector_without_database(self) -> None:
        """PostgreSQL connector requires database parameter."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            username="user",
            password="pass",
        )

        with pytest.raises(ValueError, match="database is required"):
            PostgresConnector(config)


class TestConnectionStringBuilding:
    """Test connection string generation."""

    def test_build_valid_connection_string(self) -> None:
        """Connection string is correctly formatted from configuration."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="db.example.com",
            port=5432,
            database="mydb",
            username="dbuser",
            password="dbpass",
        )

        connector = PostgresConnector(config)
        conn_str = connector._build_connection_string()

        assert (
            conn_str == "postgresql+psycopg2://dbuser:dbpass@db.example.com:5432/mydb"
        )

    def test_reject_connection_string_without_username(self) -> None:
        """Connection string requires username."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            password="pass",
        )

        connector = PostgresConnector(config)

        with pytest.raises(AuthenticationFailedError, match="username is required"):
            connector._build_connection_string()

    def test_reject_connection_string_without_password(self) -> None:
        """Connection string requires password."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
        )

        connector = PostgresConnector(config)

        with pytest.raises(AuthenticationFailedError, match="password is required"):
            connector._build_connection_string()

    def test_use_default_port_when_not_specified(self) -> None:
        """Connection string uses default port 5432 when not specified."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        conn_str = connector._build_connection_string()

        assert ":5432/" in conn_str


class TestConnectionLifecycle:
    """Test connection establishment and cleanup."""

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_connect_establishes_connection(self, mock_create_engine: Mock) -> None:
        """connect() method establishes a database connection."""
        # Setup
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()

        # Verify
        assert connector._connection is mock_connection
        assert connector._engine is mock_engine
        mock_engine.connect.assert_called_once()

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_connect_skips_if_already_connected(self, mock_create_engine: Mock) -> None:
        """connect() does nothing if already connected."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        initial_calls = mock_engine.connect.call_count

        connector.connect()

        # Should not create a new connection
        assert mock_engine.connect.call_count == initial_calls

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_disconnect_closes_connection(self, mock_create_engine: Mock) -> None:
        """disconnect() closes connection and disposes engine."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        connector.disconnect()

        # Verify cleanup
        mock_connection.close.assert_called_once()
        mock_engine.dispose.assert_called_once()
        assert connector._connection is None

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_disconnect_rolls_back_active_transaction(
        self, mock_create_engine: Mock
    ) -> None:
        """disconnect() rolls back any active transaction."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        connector._transaction_active = True

        connector.disconnect()

        # Transaction should be rolled back
        assert connector._transaction_active is False


class TestTestConnection:
    """Test connection testing functionality."""

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_test_connection_succeeds(self, mock_create_engine: Mock) -> None:
        """test_connection() returns True when connection works."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_connection.execute.return_value = None
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        result = connector.test_connection()

        assert result is True
        mock_connection.close.assert_called_once()

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_test_connection_fails_gracefully(self, mock_create_engine: Mock) -> None:
        """test_connection() returns False when connection fails."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Connection refused")
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        result = connector.test_connection()

        assert result is False


class TestQueryExecution:
    """Test query execution functionality."""

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_execute_simple_query(self, mock_create_engine: Mock) -> None:
        """execute() runs a query and returns rows as dictionaries."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        # Mock result rows
        mock_row1 = MagicMock()
        mock_row1._mapping = {"id": 1, "name": "Alice"}
        mock_row2 = MagicMock()
        mock_row2._mapping = {"id": 2, "name": "Bob"}
        mock_result = [mock_row1, mock_row2]

        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        rows = connector.execute("SELECT id, name FROM users")

        assert len(rows) == 2
        assert rows[0] == {"id": 1, "name": "Alice"}
        assert rows[1] == {"id": 2, "name": "Bob"}

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_execute_with_parameters(self, mock_create_engine: Mock) -> None:
        """execute() supports parameterized queries."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        mock_row = MagicMock()
        mock_row._mapping = {"id": 1, "name": "Alice"}
        mock_connection.execute.return_value = [mock_row]

        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        params = {"user_id": 1}
        rows = connector.execute("SELECT * FROM users WHERE id = :user_id", params)

        assert len(rows) == 1
        assert rows[0] == {"id": 1, "name": "Alice"}
        # Verify execute was called with parameters
        call_args = mock_connection.execute.call_args
        assert call_args[0][1] == params

    def test_execute_without_connection_raises_error(self) -> None:
        """execute() raises error if not connected."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)

        with pytest.raises(ConnectionFailedError, match="Not connected"):
            connector.execute("SELECT 1")

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_execute_sql_error_raises_query_execution_error(
        self, mock_create_engine: Mock
    ) -> None:
        """execute() wraps SQLAlchemy errors as QueryExecutionError."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = SQLAlchemyError("Syntax error")
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()

        with pytest.raises(QueryExecutionError, match="Failed to execute query"):
            connector.execute("INVALID SQL")


class TestTransactions:
    """Test transaction management."""

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_begin_transaction(self, mock_create_engine: Mock) -> None:
        """begin_transaction() starts a database transaction."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_connection.in_transaction.return_value = False
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        connector.begin_transaction()

        assert connector._transaction_active is True
        mock_connection.begin.assert_called_once()

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_commit_transaction(self, mock_create_engine: Mock) -> None:
        """commit() commits the active transaction."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_connection.in_transaction.return_value = True
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        connector._transaction_active = True
        connector.commit()

        assert connector._transaction_active is False
        mock_connection.commit.assert_called_once()

    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_rollback_transaction(self, mock_create_engine: Mock) -> None:
        """rollback() rolls back the active transaction."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_connection.in_transaction.return_value = True
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        connector._transaction_active = True
        connector.rollback()

        assert connector._transaction_active is False
        mock_connection.rollback.assert_called_once()


class TestMetadataDiscovery:
    """Test metadata discovery methods."""

    @patch("app.infrastructure.connectors.postgres.inspect")
    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_list_schemas(self, mock_create_engine: Mock, mock_inspect: Mock) -> None:
        """list_schemas() returns all user schemas."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_schema_names.return_value = [
            "public",
            "information_schema",
            "pg_catalog",
            "my_schema",
        ]
        mock_inspect.return_value = mock_inspector

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        schemas = connector.list_schemas()

        # System schemas should be filtered out
        assert schemas == ["public", "my_schema"]

    @patch("app.infrastructure.connectors.postgres.inspect")
    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_list_tables(self, mock_create_engine: Mock, mock_inspect: Mock) -> None:
        """list_tables() returns tables from specified schema."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users", "orders", "products"]
        mock_inspect.return_value = mock_inspector

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        tables = connector.list_tables("public")

        assert tables == ["users", "orders", "products"]
        mock_inspector.get_table_names.assert_called_once_with(schema="public")

    @patch("app.infrastructure.connectors.postgres.inspect")
    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_list_views(self, mock_create_engine: Mock, mock_inspect: Mock) -> None:
        """list_views() returns views from specified schema."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_view_names.return_value = ["user_summary", "order_stats"]
        mock_inspect.return_value = mock_inspector

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        views = connector.list_views("public")

        assert views == ["user_summary", "order_stats"]

    @patch("app.infrastructure.connectors.postgres.inspect")
    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_list_columns(self, mock_create_engine: Mock, mock_inspect: Mock) -> None:
        """list_columns() returns column metadata."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_columns.return_value = [
            {
                "name": "id",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": True,
            },
            {
                "name": "name",
                "type": "VARCHAR",
                "nullable": False,
                "primary_key": False,
            },
        ]
        mock_inspect.return_value = mock_inspector

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        columns = connector.list_columns("users", "public")

        assert len(columns) == 2
        assert isinstance(columns[0], ColumnMetadata)
        assert columns[0].name == "id"
        assert columns[0].primary_key is True
        assert columns[1].name == "name"
        assert columns[1].primary_key is False

    @patch("app.infrastructure.connectors.postgres.inspect")
    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_list_primary_keys(
        self, mock_create_engine: Mock, mock_inspect: Mock
    ) -> None:
        """list_primary_keys() returns primary key metadata."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_pk_constraint.return_value = {
            "name": "users_pkey",
            "constrained_columns": ["id"],
        }
        mock_inspect.return_value = mock_inspector

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        primary_keys = connector.list_primary_keys("users", "public")

        assert len(primary_keys) == 1
        assert isinstance(primary_keys[0], PrimaryKeyMetadata)
        assert primary_keys[0].table_name == "users"
        assert primary_keys[0].schema == "public"
        assert primary_keys[0].constraint_name == "users_pkey"
        assert primary_keys[0].column_names == ("id",)

    @patch("app.infrastructure.connectors.postgres.inspect")
    @patch("app.infrastructure.connectors.postgres.create_engine")
    def test_list_foreign_keys(
        self, mock_create_engine: Mock, mock_inspect: Mock
    ) -> None:
        """list_foreign_keys() returns foreign key metadata."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_foreign_keys.return_value = [
            {
                "name": "orders_user_id_fkey",
                "constrained_columns": ["user_id"],
                "referred_schema": "public",
                "referred_table": "users",
                "referred_columns": ["id"],
            }
        ]
        mock_inspect.return_value = mock_inspector

        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = PostgresConnector(config)
        connector.connect()
        foreign_keys = connector.list_foreign_keys("orders", "public")

        assert len(foreign_keys) == 1
        assert isinstance(foreign_keys[0], ForeignKeyMetadata)
        assert foreign_keys[0].source_table == "orders"
        assert foreign_keys[0].source_schema == "public"
        assert foreign_keys[0].name == "orders_user_id_fkey"
        assert foreign_keys[0].constrained_columns == ("user_id",)
        assert foreign_keys[0].referred_table == "users"
        assert foreign_keys[0].referred_schema == "public"
        assert foreign_keys[0].referred_columns == ("id",)


class TestConnectorRegistry:
    """Test connector registry functionality."""

    def test_create_postgres_connector(self) -> None:
        """Registry creates PostgreSQL connectors."""
        config = ConnectorConfig(
            id="test_postgres",
            name="Test Database",
            connector_type=ConnectorType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )

        connector = ConnectorRegistry.create(config)

        assert isinstance(connector, PostgresConnector)
        assert connector._config == config

    def test_unsupported_connector_type(self) -> None:
        """Registry raises error for unsupported connector types."""
        config = ConnectorConfig(
            id="test_snowflake",
            name="Test Snowflake",
            connector_type=ConnectorType.SNOWFLAKE,
            account="account",
            database="db",
            username="user",
            password="pass",
        )

        with pytest.raises(
            UnsupportedConnectorError,
            match="No connector implementation",
        ):
            ConnectorRegistry.create(config)

    def test_list_supported_connectors(self) -> None:
        """Registry lists all supported connector types."""
        supported = ConnectorRegistry.list_supported()

        assert ConnectorType.POSTGRESQL in supported

    def test_is_supported(self) -> None:
        """Registry checks if a connector type is supported."""
        assert ConnectorRegistry.is_supported(ConnectorType.POSTGRESQL) is True
        assert ConnectorRegistry.is_supported(ConnectorType.SNOWFLAKE) is False

    def test_register_custom_connector(self) -> None:
        """Registry allows registration of custom connector implementations."""
        from app.domain.connectors import DatabaseConnector

        class CustomConnector(DatabaseConnector):
            """Stub custom connector for testing."""

            def connect(self) -> None:
                pass

            def disconnect(self) -> None:
                pass

            def test_connection(self) -> bool:
                return True

            def execute(
                self, _query: str, _parameters: Mapping[str, object] | None = None
            ) -> Sequence[Mapping[str, object]]:
                return []

            def begin_transaction(self) -> None:
                pass

            def commit(self) -> None:
                pass

            def rollback(self) -> None:
                pass

            def list_schemas(self) -> list[str]:
                return []

            def list_tables(self, _schema: str | None = None) -> list[str]:
                return []

            def list_views(self, _schema: str | None = None) -> list[str]:
                return []

            def list_columns(
                self, _table_name: str, _schema: str | None = None
            ) -> list[Any]:
                return []

            def list_primary_keys(
                self, _table_name: str, _schema: str | None = None
            ) -> list[Any]:
                return []

            def list_foreign_keys(
                self, _table_name: str, _schema: str | None = None
            ) -> list[Any]:
                return []

        ConnectorRegistry.register(ConnectorType.MYSQL, CustomConnector)

        assert ConnectorRegistry.is_supported(ConnectorType.MYSQL) is True

    def test_register_invalid_connector_raises_error(self) -> None:
        """Registry rejects non-DatabaseConnector implementations."""

        class InvalidConnector:
            """Not a DatabaseConnector subclass."""

            pass

        with pytest.raises(TypeError, match="must inherit from DatabaseConnector"):
            ConnectorRegistry.register(
                ConnectorType.MYSQL,
                InvalidConnector,  # type: ignore[arg-type]
            )
