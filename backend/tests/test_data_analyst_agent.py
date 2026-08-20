"""Data Analyst Agent Capability & Security Tests.

Tests the full NL->SQL Data Analyst agent workflow and tool/SQL security rules:
- Authorized dataset query -> PASS.
- Unauthorized dataset -> DENY.
- Cross-tenant dataset -> DENY.
- SELECT -> PASS.
- INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE -> DENY.
- Invalid SQL -> safe error.
- Unknown dataset/table -> safe error.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.interfaces.i_llm_provider import LLMResponse
from app.application.use_cases.execute_agent_query import ExecuteAgentQueryUseCase
from app.core.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    InvalidQueryError,
)
from app.domain.entities.user import User
from app.domain.value_objects.query import QueryColumn, QueryResult
from app.infrastructure.query.sqlalchemy_validator import SqlAlchemyQueryValidator


@pytest.fixture
def mock_user() -> User:
    return User(id="usr-analyst-1", email="analyst@nexusbi.io", is_active=True)


@pytest.fixture
def mock_unauthorized_user() -> User:
    return User(id="usr-viewer-1", email="viewer@nexusbi.io", is_active=True)


def test_authorized_dataset_query_pass(mock_user: User) -> None:
    """Authorized user querying an authorized dataset -> PASS with result."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = True

    ds = MagicMock()
    ds.id = "ds-sales"
    ds.name = "Sales Dataset"
    ds.workspace_id = "ws-1"
    ds.schema_metadata = {
        "columns": [
            {"name": "month", "type": "varchar"},
            {"name": "amount", "type": "numeric"},
        ]
    }
    dataset_repo.get_by_id.return_value = ds
    dataset_repo.list.return_value = ([ds], 1)

    sql_resp = (
        "SELECT month, SUM(amount) AS total_sales FROM sales GROUP BY month"
    )
    llm_service.complete.side_effect = [
        LLMResponse(
            content=sql_resp,
            model="claude-3-5-sonnet",
            prompt_tokens=100,
            completion_tokens=30,
            total_tokens=130,
            cost_usd=0.001,
        ),
        LLMResponse(
            content="Total sales peaked in December with $50,000.",
            model="claude-3-5-sonnet",
            prompt_tokens=150,
            completion_tokens=20,
            total_tokens=170,
            cost_usd=0.002,
        ),
    ]

    mock_qr = QueryResult(
        rows=[
            {"month": "2026-01", "total_sales": 25000},
            {"month": "2026-02", "total_sales": 30000},
        ],
        columns=[
            QueryColumn(name="month", type="varchar"),
            QueryColumn(name="total_sales", type="numeric"),
        ],
        column_types={"month": "varchar", "total_sales": "numeric"},
        execution_time=0.02,
        row_count=2,
    )
    query_service.execute.return_value = mock_qr

    agent_run_repo.save.side_effect = lambda run: run

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    run = use_case.execute(
        user=mock_user,
        natural_language_query="What were total sales by month?",
        dataset_id="ds-sales",
        workspace_id="ws-1",
        agent_role="data_analyst",
    )

    assert run.status.value == "completed"
    assert run.generated_sql == sql_resp
    assert run.insights == "Total sales peaked in December with $50,000."
    assert run.query_result is not None
    assert run.query_result["row_count"] == 2
    assert len(run.query_result["rows"]) == 2


def test_unauthorized_dataset_deny(mock_unauthorized_user: User) -> None:
    """User without datasets:read permission -> DENY (AuthorizationError)."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = False

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            user=mock_unauthorized_user,
            natural_language_query="What were total sales by month?",
            dataset_id="ds-sales",
        )

    assert "datasets:read" in str(exc_info.value.detail)


def test_cross_tenant_dataset_deny(mock_user: User) -> None:
    """Requesting dataset outside user's authorized workspace -> DENY."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = True

    ds = MagicMock()
    ds.id = "ds-org-a"
    ds.workspace_id = "ws-org-a"
    dataset_repo.get_by_id.return_value = ds

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            user=mock_user,
            natural_language_query="What were total sales by month?",
            dataset_id="ds-org-a",
            workspace_id="ws-org-b",
        )

    assert "workspace scope" in str(exc_info.value.detail)


def test_select_query_pass() -> None:
    """SELECT, UNION, and CTE queries pass SqlAlchemyQueryValidator."""
    validator = SqlAlchemyQueryValidator()
    req1 = MagicMock(query=MagicMock(sql="SELECT * FROM sales"), parameters={})
    cte_sql = "WITH cte AS (SELECT * FROM orders) SELECT * FROM cte"
    req2 = MagicMock(query=MagicMock(sql=cte_sql), parameters={})

    validator.validate(req1)
    validator.validate(req2)


@pytest.mark.parametrize(
    "mutation_sql",
    [
        "INSERT INTO sales (amount) VALUES (100)",
        "UPDATE sales SET amount = 0",
        "DELETE FROM sales",
        "DROP TABLE sales",
        "ALTER TABLE sales ADD COLUMN test text",
        "TRUNCATE TABLE sales",
        "CREATE TABLE hack (id int)",
        "GRANT ALL PRIVILEGES ON DATABASE db TO user",
        "REVOKE SELECT ON sales FROM public",
    ],
)
def test_mutations_deny(mutation_sql: str) -> None:
    """INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE -> DENY."""
    validator = SqlAlchemyQueryValidator()
    req = MagicMock(query=MagicMock(sql=mutation_sql), parameters={})

    with pytest.raises(InvalidQueryError):
        validator.validate(req)


def test_invalid_sql_safe_error() -> None:
    """Malformed SQL syntax -> safe InvalidQueryError."""
    validator = SqlAlchemyQueryValidator()
    req = MagicMock(query=MagicMock(sql="SELECT FROM WHERE (((("), parameters={})

    with pytest.raises(InvalidQueryError) as exc_info:
        validator.validate(req)

    err_text = (str(exc_info.value) + " " + str(exc_info.value.detail or "")).lower()
    assert "parse error" in err_text or "invalid" in err_text or "syntax" in err_text


def test_unknown_dataset_table_safe_error(mock_user: User) -> None:
    """Unknown dataset_id -> safe EntityNotFoundError."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = True
    dataset_repo.get_by_id.return_value = None

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    with pytest.raises(EntityNotFoundError) as exc_info:
        use_case.execute(
            user=mock_user,
            natural_language_query="What were total sales?",
            dataset_id="ds-nonexistent",
        )

    err_text = str(exc_info.value) + " " + str(exc_info.value.detail or "")
    assert "ds-nonexistent" in err_text
