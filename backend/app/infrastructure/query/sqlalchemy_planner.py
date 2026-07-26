"""SQLAlchemy query planner implementation."""

from __future__ import annotations

import json

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.application.interfaces.i_query_planner import IQueryPlanner
from app.core.exceptions import InvalidQueryError
from app.domain.value_objects.query import (
    QueryMetadata,
    QueryRequest,
    QueryStatistics,
)


class SqlAlchemyQueryPlanner(IQueryPlanner):
    """Query planner executing EXPLAIN queries via SQLAlchemy."""

    def __init__(self, engine: Engine | Connection) -> None:
        self.engine = engine

    def plan(self, request: QueryRequest) -> QueryMetadata:
        """Generate execution plan metadata using database EXPLAIN commands."""
        raw_sql = request.query.sql.strip().rstrip(";")
        explain_sql = f"EXPLAIN {raw_sql}"
        statement = text(explain_sql)

        plan_output: str | None = None
        try:
            conn = (
                self.engine
                if isinstance(self.engine, Connection)
                else self.engine.connect()
            )
            try:
                result = conn.execute(statement, request.parameters)
                rows = result.fetchall()
                lines = []
                for row in rows:
                    if len(row) == 1:
                        val = row[0]
                        line = (
                            json.dumps(val)
                            if isinstance(val, (dict, list))
                            else str(val)
                        )
                        lines.append(line)
                    else:
                        lines.append(" | ".join(str(item) for item in row))
                plan_output = "\n".join(lines)
            finally:
                if isinstance(self.engine, Engine):
                    conn.close()
        except SQLAlchemyError as exc:
            err_msg = str(exc)
            if "syntax" in err_msg.lower() or "does not exist" in err_msg.lower():
                raise InvalidQueryError(f"Query planning failed: {err_msg}") from exc
            plan_output = f"Plan unavailable: {err_msg}"

        stats = QueryStatistics(
            query_plan=plan_output,
            rows_scanned=None,
            bytes_processed=None,
            cache_hit=False,
        )

        return QueryMetadata(
            statistics=stats,
            execution_time=0.0,
            row_count=0,
            columns=[],
            truncated=False,
            limit=request.get_effective_limit(),
            offset=request.get_effective_offset(),
        )
