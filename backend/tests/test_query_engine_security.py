"""Security and injection attack unit tests for Universal Query Engine."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import StaticPool

from app.core.exceptions import InvalidQueryError
from app.domain.value_objects.query import QueryRequest
from app.infrastructure.query.sqlalchemy_executor import SqlAlchemyQueryExecutor
from app.infrastructure.query.sqlalchemy_validator import SqlAlchemyQueryValidator


@pytest.fixture
def db_engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE sensitive_data (  id INT PRIMARY KEY,  secret_token TEXT)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO sensitive_data (id, secret_token) "
                "VALUES (1, 'topsecret_123')"
            )
        )
        conn.commit()
    return engine


@pytest.fixture
def validator() -> SqlAlchemyQueryValidator:
    return SqlAlchemyQueryValidator()


@pytest.mark.parametrize(
    "injection_query",
    [
        "SELECT * FROM sensitive_data WHERE secret_token = '' OR '1'='1'",
        "SELECT * FROM sensitive_data; DROP TABLE sensitive_data;",
        "SELECT * FROM sensitive_data -- DROP TABLE sensitive_data",
        "SELECT * FROM sensitive_data UNION SELECT 1, 'hacked'",
        "INSERT INTO sensitive_data (id, secret_token) VALUES (2, 'malicious')",
        "DELETE FROM sensitive_data",
        "UPDATE sensitive_data SET secret_token = 'hacked'",
        "ALTER TABLE sensitive_data DROP COLUMN secret_token",
        "TRUNCATE TABLE sensitive_data",
    ],
)
def test_security_validation_blocks_unsafe_queries(
    validator: SqlAlchemyQueryValidator, injection_query: str
) -> None:
    req = QueryRequest.create(injection_query)
    if "SELECT" in injection_query.upper() and not any(
        kw in injection_query.upper()
        for kw in ["DROP", "INSERT", "DELETE", "UPDATE", "ALTER", "TRUNCATE", ";"]
    ):
        validator.validate(req)
    else:
        with pytest.raises(InvalidQueryError):
            validator.validate(req)


def test_sql_parameter_binding_prevents_sql_injection(db_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(db_engine)
    validator = SqlAlchemyQueryValidator()

    malicious_input = "' OR '1'='1"

    req = QueryRequest.create(
        "SELECT * FROM sensitive_data WHERE secret_token = :token",
        parameters={"token": malicious_input},
    )

    validator.validate(req)
    res = executor.execute(req)

    assert res.row_count == 0
    assert len(res.rows) == 0


def test_parameter_binding_with_quotes_and_special_chars(db_engine: Engine) -> None:
    executor = SqlAlchemyQueryExecutor(db_engine)

    special_token = "O'Connor & Sons; DROP TABLE test--"
    req = QueryRequest.create(
        "SELECT * FROM sensitive_data WHERE secret_token = :token",
        parameters={"token": special_token},
    )
    res = executor.execute(req)

    assert res.row_count == 0
    check_req = QueryRequest.create("SELECT COUNT(*) AS cnt FROM sensitive_data")
    check_res = executor.execute(check_req)
    assert check_res.rows[0]["cnt"] == 1
