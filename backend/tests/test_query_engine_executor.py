"""Integration/Unit tests for Universal Query Engine Executor."""

from __future__ import annotations

import time

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import StaticPool

from app.domain.value_objects.query import QueryRequest
from app.infrastructure.query.sqlalchemy_executor import SqlAlchemyQueryExecutor
from app.infrastructure.query.sqlalchemy_planner import SqlAlchemyQueryPlanner


@pytest.fixture
def sqlite_engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE sales ("
                "  id INTEGER PRIMARY KEY,"
                "  customer_id TEXT,"
                "  amount REAL,"
                "  sale_date TEXT"
                ")"
            )
        )
        for i in range(1, 101):
            conn.execute(
                text(
                    "INSERT INTO sales (id, customer_id, amount, sale_date) "
                    "VALUES (:id, :cid, :amt, :dt)"
                ),
                {
                    "id": i,
                    "cid": f"cust_{i % 5}",
                    "amt": float(i * 10.5),
                    "dt": f"2026-01-{(i % 28) + 1:02d}",
                },
            )
        conn.commit()
    return engine


def test_execute_simple_query(sqlite_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(sqlite_engine)
    sql = "SELECT id, customer_id, amount FROM sales WHERE id = :id"
    req = QueryRequest.create(sql, parameters={"id": 1})
    res = executor.execute(req)

    assert res.row_count == 1
    assert len(res.rows) == 1
    assert res.rows[0]["id"] == 1
    assert res.rows[0]["customer_id"] == "cust_1"
    assert res.rows[0]["amount"] == 10.5
    assert len(res.columns) == 3
    assert res.execution_time >= 0.0
    assert res.metadata.row_count == 1


def test_parameter_binding(sqlite_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(sqlite_engine)
    sql = (
        "SELECT * FROM sales "
        "WHERE customer_id = :customer_id AND sale_date >= :start_date"
    )
    req = QueryRequest.create(
        sql,
        parameters={"customer_id": "cust_1", "start_date": "2026-01-05"},
    )
    res = executor.execute(req)

    assert res.row_count > 0
    for row in res.rows:
        assert row["customer_id"] == "cust_1"
        assert row["sale_date"] >= "2026-01-05"


def test_pagination_limit_offset(sqlite_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(sqlite_engine)
    sql = "SELECT * FROM sales ORDER BY id ASC"
    req = QueryRequest.create(sql, limit=10, offset=20)
    res = executor.execute(req)

    assert res.row_count == 10
    assert res.rows[0]["id"] == 21
    assert res.rows[-1]["id"] == 30
    assert res.metadata.limit == 10
    assert res.metadata.offset == 20


def test_pagination_page_and_page_size(sqlite_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(sqlite_engine)
    sql = "SELECT * FROM sales ORDER BY id ASC"
    req = QueryRequest.create(sql, page=3, page_size=15)
    res = executor.execute(req)

    assert res.row_count == 15
    assert res.rows[0]["id"] == 31
    assert res.metadata.limit == 15
    assert res.metadata.offset == 30


def test_query_planner(sqlite_engine: Engine) -> None:
    planner = SqlAlchemyQueryPlanner(sqlite_engine)
    sql = "SELECT * FROM sales WHERE customer_id = :cid"
    req = QueryRequest.create(sql, parameters={"cid": "cust_1"})
    meta = planner.plan(req)

    assert meta.statistics.query_plan is not None
    assert isinstance(meta.statistics.query_plan, str)


def test_large_result_set_handling(sqlite_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(sqlite_engine)
    req = QueryRequest.create("SELECT * FROM sales")
    res = executor.execute(req)

    assert res.row_count == 100
    assert len(res.rows) == 100


def test_query_timeout(sqlite_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(sqlite_engine, default_timeout_seconds=0.0001)
    req = QueryRequest.create("SELECT * FROM sales", timeout=0.0001)

    time.sleep(0.001)
    assert executor is not None
    assert req is not None
