"""Unit tests for Universal Query Engine SQL Validator."""

from __future__ import annotations

import pytest

from app.core.exceptions import InvalidQueryError
from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.query import QueryRequest
from app.infrastructure.query.sqlalchemy_validator import SqlAlchemyQueryValidator


@pytest.fixture
def validator() -> SqlAlchemyQueryValidator:
    return SqlAlchemyQueryValidator()


def test_valid_simple_select(validator: SqlAlchemyQueryValidator) -> None:
    req = QueryRequest.create("SELECT 1 AS val")
    validator.validate(req)


def test_valid_cte_select(validator: SqlAlchemyQueryValidator) -> None:
    req = QueryRequest.create("WITH cte AS (SELECT 1 AS a) SELECT a FROM cte")
    validator.validate(req)


def test_valid_select_with_named_parameters(
    validator: SqlAlchemyQueryValidator,
) -> None:
    sql = (
        "SELECT * FROM orders WHERE customer_id = :customer_id AND date >= :start_date"
    )
    req = QueryRequest.create(
        sql,
        parameters={"customer_id": "cust_123", "start_date": "2026-01-01"},
    )
    validator.validate(req)


def test_valid_subquery(validator: SqlAlchemyQueryValidator) -> None:
    sql = "SELECT * FROM (SELECT id, name FROM users) AS u WHERE u.id = :uid"
    req = QueryRequest.create(sql, parameters={"uid": 1})
    validator.validate(req)


@pytest.mark.parametrize(
    "forbidden_sql",
    [
        "INSERT INTO users (id, name) VALUES ('1', 'Alice')",
        "UPDATE users SET name = 'Bob' WHERE id = '1'",
        "DELETE FROM users WHERE id = '1'",
        "DROP TABLE users",
        "ALTER TABLE users ADD COLUMN age INT",
        "TRUNCATE TABLE users",
        "CREATE TABLE test (id INT)",
        "EXEC sp_executesql 'SELECT 1'",
        "EXECUTE IMMEDIATE 'DROP TABLE users'",
        "MERGE INTO target USING source ON target.id = source.id",
        "CALL procedure_name()",
        "GRANT ALL PRIVILEGES ON users TO public",
        "REVOKE ALL ON users FROM public",
        "VACUUM FULL",
    ],
)
def test_reject_forbidden_statements(
    validator: SqlAlchemyQueryValidator, forbidden_sql: str
) -> None:
    req = QueryRequest.create(forbidden_sql)
    with pytest.raises(InvalidQueryError):
        validator.validate(req)


def test_reject_multiple_statements(validator: SqlAlchemyQueryValidator) -> None:
    req = QueryRequest.create("SELECT 1; SELECT 2;")
    with pytest.raises(InvalidQueryError, match="Multiple SQL statements"):
        validator.validate(req)


def test_reject_sql_injection_attempt_with_semicolon(
    validator: SqlAlchemyQueryValidator,
) -> None:
    req = QueryRequest.create("SELECT * FROM users; DROP TABLE users;")
    with pytest.raises(InvalidQueryError):
        validator.validate(req)


def test_reject_empty_query() -> None:
    with pytest.raises(
        DomainValidationError, match="Query SQL string must not be empty"
    ):
        QueryRequest.create("   ")


def test_reject_invalid_parameter_names(validator: SqlAlchemyQueryValidator) -> None:
    req = QueryRequest.create("SELECT 1", parameters={"123-invalid": "val"})
    with pytest.raises(InvalidQueryError, match="Invalid parameter name"):
        validator.validate(req)
