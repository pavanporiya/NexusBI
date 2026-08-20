"""Data Analyst Visualization Capability Tests.

Verifies:
1. Valid line chart -> PASS.
2. Valid bar chart -> PASS.
3. Invalid chart type -> DENY.
4. Malformed chart JSON -> validation error.
5. Unauthorized dataset -> DENY.
6. Cross-tenant data -> DENY.
7. Existing chart APIs remain working.
8. Existing agent/security tests remain passing.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.application.interfaces.i_llm_provider import LLMResponse
from app.application.services.visualization_service import VisualizationService
from app.application.use_cases.execute_agent_query import ExecuteAgentQueryUseCase
from app.core.exceptions import AuthorizationError, ValidationError
from app.domain.entities.user import User
from app.domain.value_objects.chart_spec import ChartSpec
from app.domain.value_objects.query import QueryColumn, QueryResult


@pytest.fixture
def mock_user() -> User:
    return User(id="usr-analyst-1", email="analyst@nexusbi.io", is_active=True)


@pytest.fixture
def mock_unauthorized_user() -> User:
    return User(id="usr-viewer-1", email="viewer@nexusbi.io", is_active=True)


@pytest.fixture
def sample_query_result() -> QueryResult:
    return QueryResult(
        rows=[
            {"month": "2026-01", "sales": 10000},
            {"month": "2026-02", "sales": 15000},
            {"month": "2026-03", "sales": 20000},
        ],
        columns=[
            QueryColumn(name="month", type="varchar"),
            QueryColumn(name="sales", type="numeric"),
        ],
        column_types={"month": "varchar", "sales": "numeric"},
        execution_time=0.01,
        row_count=3,
    )


@pytest.fixture
def sample_categorical_result() -> QueryResult:
    return QueryResult(
        rows=[
            {"region": "North America", "revenue": 45000},
            {"region": "Europe", "revenue": 35000},
            {"region": "Asia", "revenue": 55000},
        ],
        columns=[
            QueryColumn(name="region", type="varchar"),
            QueryColumn(name="revenue", type="numeric"),
        ],
        column_types={"region": "varchar", "revenue": "numeric"},
        execution_time=0.01,
        row_count=3,
    )


# 1. Valid line chart -> PASS
def test_valid_line_chart_pass(sample_query_result: QueryResult) -> None:
    service = VisualizationService()
    spec = service.generate_chart_specification(
        natural_language_query="Show monthly sales for this year",
        query_result=sample_query_result,
        override_type="line",
    )

    assert spec["type"] == "line"
    assert spec["title"] == "Show monthly sales for this year"
    assert spec["x_axis"] == "month"
    assert spec["y_axis"] == "sales"
    assert len(spec["data"]) == 3
    validated = ChartSpec(**spec)
    assert validated.type == "line"


# 2. Valid bar chart -> PASS
def test_valid_bar_chart_pass(sample_categorical_result: QueryResult) -> None:
    service = VisualizationService()
    spec = service.generate_chart_specification(
        natural_language_query="Show revenue by region",
        query_result=sample_categorical_result,
        override_type="bar",
    )

    assert spec["type"] == "bar"
    assert spec["x_axis"] == "region"
    assert spec["y_axis"] == "revenue"
    assert len(spec["data"]) == 3
    validated = ChartSpec(**spec)
    assert validated.type == "bar"


# 3. Invalid chart type -> DENY
def test_invalid_chart_type_deny(sample_query_result: QueryResult) -> None:
    service = VisualizationService()
    with pytest.raises(ValidationError) as exc_info:
        service.generate_chart_specification(
            natural_language_query="Show monthly sales",
            query_result=sample_query_result,
            override_type="invalid_chart_type_123",
        )

    assert "Unsupported chart type" in str(exc_info.value.message)


# 4. Malformed chart JSON -> validation error
def test_malformed_chart_json_validation_error() -> None:
    with pytest.raises(PydanticValidationError):
        # Missing required title and type
        ChartSpec(type="", title="")

    with pytest.raises(PydanticValidationError):
        # Unsupported type
        ChartSpec(type="scatter_plot_bogus", title="Title", data=[])


# 5. Unauthorized dataset -> DENY
def test_unauthorized_dataset_deny(mock_unauthorized_user: User) -> None:
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

    with pytest.raises(AuthorizationError):
        use_case.execute(
            user=mock_unauthorized_user,
            natural_language_query="Show monthly sales for this year",
            dataset_id="ds-sales",
        )


# 6. Cross-tenant data -> DENY
def test_cross_tenant_data_deny(mock_user: User) -> None:
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

    with pytest.raises(AuthorizationError):
        use_case.execute(
            user=mock_user,
            natural_language_query="Show monthly sales",
            dataset_id="ds-org-a",
            workspace_id="ws-org-b",
        )


# 7. Agent integration produces SQL result + chart specification
def test_data_analyst_agent_generates_sql_and_chart_spec(mock_user: User) -> None:
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
            {"name": "sales", "type": "numeric"},
        ]
    }
    dataset_repo.get_by_id.return_value = ds

    llm_service.complete.side_effect = [
        LLMResponse(
            content="SELECT month, SUM(sales) AS sales FROM sales_fact GROUP BY month",
            model="claude-3-5-sonnet",
            prompt_tokens=100,
            completion_tokens=30,
            total_tokens=130,
            cost_usd=0.001,
        ),
        LLMResponse(
            content="Monthly sales showed consistent growth peaking in March.",
            model="claude-3-5-sonnet",
            prompt_tokens=150,
            completion_tokens=20,
            total_tokens=170,
            cost_usd=0.002,
        ),
    ]

    mock_qr = QueryResult(
        rows=[
            {"month": "2026-01", "sales": 10000},
            {"month": "2026-02", "sales": 15000},
            {"month": "2026-03", "sales": 20000},
        ],
        columns=[
            QueryColumn(name="month", type="varchar"),
            QueryColumn(name="sales", type="numeric"),
        ],
        column_types={"month": "varchar", "sales": "numeric"},
        execution_time=0.02,
        row_count=3,
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
        natural_language_query="Show monthly sales for this year",
        dataset_id="ds-sales",
        workspace_id="ws-1",
        agent_role="data_analyst",
    )

    assert run.status.value == "completed"
    assert run.generated_sql is not None
    assert run.insights == "Monthly sales showed consistent growth peaking in March."
    assert run.visualization_config is not None
    assert run.visualization_config["type"] in ("line", "bar")
    assert run.visualization_config["x_axis"] == "month"
    assert run.visualization_config["y_axis"] == "sales"
    assert len(run.visualization_config["data"]) == 3
