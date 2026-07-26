"""SQLAlchemy-based query executor implementation."""

from __future__ import annotations

import concurrent.futures
import time
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import (
    OperationalError,
    SQLAlchemyError,
    TimeoutError as SATimeoutError,
)

from app.application.interfaces.i_query_executor import IQueryExecutor
from app.core.exceptions import (
    InvalidQueryError,
    QueryExecutionError,
    QueryTimeoutError,
)
from app.domain.value_objects.query import (
    QueryColumn,
    QueryMetadata,
    QueryRequest,
    QueryResult,
    QueryStatistics,
)

DEFAULT_TIMEOUT_SECONDS = 30.0


def _serialize_value(val: Any) -> Any:
    """Convert non-JSON serializable database values to Python primitives."""
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return val


class SqlAlchemyQueryExecutor(IQueryExecutor):
    """Execution engine for executing parameterized read-only queries."""

    def __init__(
        self,
        engine: Engine | Connection,
        default_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.engine = engine
        self.default_timeout_seconds = default_timeout_seconds

    def execute(self, request: QueryRequest) -> QueryResult:
        """Execute query with parameters, pagination, and timeout bounds."""
        timeout_sec = (
            request.timeout
            if request.timeout is not None
            else self.default_timeout_seconds
        )

        def _run_query() -> QueryResult:
            start_time = time.perf_counter()
            params = dict(request.parameters)
            raw_sql = request.query.sql.rstrip(";").strip()

            effective_limit = request.get_effective_limit()
            effective_offset = request.get_effective_offset()

            # Apply pagination via subquery wrapper if limit or offset specified
            if effective_limit is not None or effective_offset is not None:
                wrapper_sql = f"SELECT * FROM ({raw_sql}) AS __query_wrapper"
                if effective_limit is not None:
                    wrapper_sql += " LIMIT :__limit"
                    params["__limit"] = effective_limit
                if effective_offset is not None:
                    wrapper_sql += " OFFSET :__offset"
                    params["__offset"] = effective_offset
                executable_sql = wrapper_sql
            else:
                executable_sql = raw_sql

            try:
                conn = (
                    self.engine
                    if isinstance(self.engine, Connection)
                    else self.engine.connect()
                )
                try:
                    dialect_name = getattr(conn.dialect, "name", "")
                    if dialect_name == "postgresql" and timeout_sec > 0:
                        timeout_ms = int(timeout_sec * 1000)
                        conn.execute(
                            text(f"SET LOCAL statement_timeout = {timeout_ms}")
                        )

                    statement = text(executable_sql)
                    cursor_result = conn.execute(statement, params)

                    columns: list[QueryColumn] = []
                    column_types: dict[str, str] = {}

                    if cursor_result.returns_rows:
                        raw_desc = (
                            cursor_result.cursor.description
                            if cursor_result.cursor
                            and hasattr(cursor_result.cursor, "description")
                            else None
                        )
                        if raw_desc:
                            for col_desc in raw_desc:
                                col_name = str(col_desc[0])
                                col_type = (
                                    str(col_desc[1])
                                    if len(col_desc) > 1 and col_desc[1]
                                    else "string"
                                )
                                q_col = QueryColumn(name=col_name, type=col_type)
                                columns.append(q_col)
                                column_types[col_name] = q_col.type
                        else:
                            for col_name in cursor_result.keys():
                                q_col = QueryColumn(name=str(col_name), type="unknown")
                                columns.append(q_col)
                                column_types[str(col_name)] = "unknown"

                        raw_rows = cursor_result.fetchall()
                        formatted_rows: list[dict[str, Any]] = []
                        for row in raw_rows:
                            row_dict = {}
                            for col_name, val in row._mapping.items():
                                row_dict[str(col_name)] = _serialize_value(val)
                            formatted_rows.append(row_dict)
                    else:
                        formatted_rows = []

                    execution_time = time.perf_counter() - start_time
                    row_count = len(formatted_rows)

                    metadata = QueryMetadata(
                        statistics=QueryStatistics(
                            query_plan=None,
                            rows_scanned=row_count,
                            bytes_processed=None,
                            cache_hit=False,
                        ),
                        execution_time=execution_time,
                        row_count=row_count,
                        columns=columns,
                        truncated=False,
                        limit=effective_limit,
                        offset=effective_offset,
                    )

                    return QueryResult(
                        rows=formatted_rows,
                        columns=columns,
                        column_types=column_types,
                        execution_time=execution_time,
                        row_count=row_count,
                        metadata=metadata,
                    )
                finally:
                    if isinstance(self.engine, Engine):
                        conn.close()
            except (SATimeoutError, OperationalError) as exc:
                err_str = str(exc).lower()
                if (
                    "timeout" in err_str
                    or "canceled" in err_str
                    or "canceling statement" in err_str
                ):
                    raise QueryTimeoutError(
                        timeout_seconds=timeout_sec, detail=str(exc)
                    ) from exc
                if "no such table" in err_str or "syntax" in err_str:
                    raise InvalidQueryError(f"Query error: {exc}") from exc
                raise QueryExecutionError(
                    message="Database operational error", detail=str(exc)
                ) from exc
            except SQLAlchemyError as exc:
                raise QueryExecutionError(
                    message="Database execution failure", detail=str(exc)
                ) from exc

        if timeout_sec > 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_run_query)
                try:
                    return future.result(timeout=timeout_sec)
                except concurrent.futures.TimeoutError as exc:
                    raise QueryTimeoutError(
                        timeout_seconds=timeout_sec,
                        detail=f"Query execution timed out after {timeout_sec}s.",
                    ) from exc
        else:
            return _run_query()
