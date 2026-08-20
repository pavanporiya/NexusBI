"""Agent Gateway REST API endpoints (v1 namespace)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_user, require_permission
from app.api.dependencies.auth import (
    get_execute_agent_query_use_case,
    get_get_agent_run_use_case,
    get_list_agent_runs_use_case,
)
from app.application.dto.agent_dto import (
    AgentPersonaSummaryDTO,
    AgentQueryRequestDTO,
    AgentQueryResponseDTO,
    AgentQueryResultDTO,
    AgentRunSummaryDTO,
    StepRecordDTO,
)
from app.application.dto.error_dto import create_error_responses
from app.application.use_cases.execute_agent_query import ExecuteAgentQueryUseCase
from app.application.use_cases.get_agent_run import (
    GetAgentRunUseCase,
    ListAgentRunsUseCase,
)
from app.domain.entities.agent_run import AgentPersona, AgentRun
from app.domain.entities.user import User

router = APIRouter(prefix="/agents", tags=["AI Agent Gateway"])


def _map_run_to_response_dto(run: AgentRun) -> AgentQueryResponseDTO:
    """Map AgentRun domain entity to response DTO."""
    steps_dto = [
        StepRecordDTO(
            step_name=s.step_name,
            status=s.status,
            started_at=s.started_at,
            completed_at=s.completed_at,
            latency_ms=s.latency_ms,
            error=s.error,
        )
        for s in run.steps
    ]

    result_dto: AgentQueryResultDTO | None = None
    if run.query_result and isinstance(run.query_result, dict):
        result_dto = AgentQueryResultDTO(
            rows=run.query_result.get("rows", []),
            columns=run.query_result.get("columns", []),
            row_count=run.query_result.get("row_count", 0),
            execution_time_ms=run.query_result.get("execution_time_ms", 0.0),
            truncated=run.query_result.get("truncated", False),
        )

    return AgentQueryResponseDTO(
        run_id=run.id,
        status=run.status.value,
        agent_role=run.agent_role,
        natural_language_query=run.natural_language_query,
        generated_sql=run.generated_sql,
        insights=run.insights,
        visualization_config=run.visualization_config or None,
        code_snippet=run.code_snippet,
        result=result_dto,
        confidence=run.confidence,
        total_tokens=run.total_tokens,
        total_cost_usd=run.total_cost_usd,
        steps=steps_dto,
        error=run.error,
        created_at=run.created_at,
    )


@router.get(
    "/personas",
    response_model=list[AgentPersonaSummaryDTO],
    status_code=status.HTTP_200_OK,
    summary="List Available Specialist Agent Personas",
    operation_id="agent_list_personas",
    response_description="List of available specialist personas.",
    responses=create_error_responses(401, 403, 500),
    description="Fetch all supported Agency Agent specialist personas in NexusBI.",
    dependencies=[Depends(require_permission("agents:read"))],
)
def list_agent_personas() -> list[AgentPersonaSummaryDTO]:
    """Retrieve metadata for available specialist agent personas."""
    return [
        AgentPersonaSummaryDTO(
            role=AgentPersona.SQL_DATA.value,
            name="SQL / Data Agent",
            description=(
                "Precision read-only SQL generation, syntax validation, "
                "and schema mapping."
            ),
        ),
        AgentPersonaSummaryDTO(
            role=AgentPersona.DATA_ANALYST.value,
            name="Data Analyst Agent",
            description=(
                "Transforms query results into statistical summaries, "
                "trends, and business insights."
            ),
        ),
        AgentPersonaSummaryDTO(
            role=AgentPersona.DASHBOARD_BI.value,
            name="Dashboard / BI Agent",
            description=(
                "Recommends optimal chart visual types, titles, axes, "
                "and widget placement."
            ),
        ),
        AgentPersonaSummaryDTO(
            role=AgentPersona.CODE_ENGINEERING.value,
            name="Code / Engineering Agent",
            description=(
                "Generates Python/SQL data engineering scripts, CTEs, "
                "and ETL pipelines."
            ),
        ),
        AgentPersonaSummaryDTO(
            role=AgentPersona.ORCHESTRATOR.value,
            name="Orchestrator Agent",
            description=(
                "Coordinates multi-agent query execution, insight "
                "extraction, and visual recommendation."
            ),
        ),
    ]


@router.post(
    "/query",
    response_model=AgentQueryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Execute Agent Query",
    operation_id="agent_execute_query",
    response_description="Agent execution results with generated SQL and trace steps.",
    responses=create_error_responses(400, 401, 403, 404, 500, 504),
    description=(
        "Translates natural language to SQL and executes it via "
        "the agent pipeline."
    ),
    dependencies=[Depends(require_permission("agents:execute"))],
)
def execute_agent_query(
    dto: AgentQueryRequestDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[
        ExecuteAgentQueryUseCase, Depends(get_execute_agent_query_use_case)
    ],
) -> AgentQueryResponseDTO:
    """Submit a natural language question to the AI Agent pipeline."""
    run = use_case.execute(
        user=current_user,
        natural_language_query=dto.natural_language_query,
        dataset_id=dto.dataset_id,
        workspace_id=dto.workspace_id,
        agent_role=dto.agent_role,
    )
    return _map_run_to_response_dto(run)


@router.get(
    "/runs/{run_id}",
    response_model=AgentQueryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get Agent Run Details",
    operation_id="agent_get_run",
    response_description="Detailed agent run state.",
    responses=create_error_responses(401, 403, 404, 500),
    description="Fetch a specific agent run's status and execution details.",
    dependencies=[Depends(require_permission("agents:read"))],
)
def get_agent_run(
    run_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[GetAgentRunUseCase, Depends(get_get_agent_run_use_case)],
) -> AgentQueryResponseDTO:
    """Retrieve agent run details by run ID."""
    run = use_case.execute(run_id=run_id, user_id=current_user.id)
    return _map_run_to_response_dto(run)


@router.get(
    "/runs",
    response_model=list[AgentRunSummaryDTO],
    status_code=status.HTTP_200_OK,
    summary="List User Agent Runs",
    operation_id="agent_list_runs",
    response_description="Paginated list of user's agent runs.",
    responses=create_error_responses(401, 403, 500),
    description="Fetch user's historical agent runs.",
    dependencies=[Depends(require_permission("agents:read"))],
)
def list_agent_runs(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListAgentRunsUseCase, Depends(get_list_agent_runs_use_case)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AgentRunSummaryDTO]:
    """List agent runs for the current authenticated user."""
    runs = use_case.execute(user_id=current_user.id, limit=limit, offset=offset)
    return [
        AgentRunSummaryDTO(
            run_id=r.id,
            status=r.status.value,
            agent_role=r.agent_role,
            natural_language_query=r.natural_language_query,
            generated_sql=r.generated_sql,
            confidence=r.confidence,
            total_tokens=r.total_tokens,
            created_at=r.created_at,
        )
        for r in runs
    ]

