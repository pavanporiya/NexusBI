"""Execute Agent Query use case.

Orchestrates the NL→SQL agent pipeline:
1. Resolve dataset schema
2. Generate SQL via LLM
3. Validate SQL via existing QueryService
4. Execute SQL via existing QueryService
5. Persist the AgentRun

This is a sequential chain (simplest topology from the Multi-Agent
Systems Architect pattern) with structured state at each step.
"""

from __future__ import annotations

import re
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from app.application.interfaces.i_llm_provider import LLMResponse
from app.application.services.agent_tool_registry import AgentToolRegistry
from app.application.services.interfaces import IAuthorizationService
from app.application.services.query_service import QueryService
from app.core.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    NexusBIError,
    PromptInjectionError,
    ValidationError,
)
from app.core.logging import AuditLogger, get_logger
from app.domain.entities.agent_run import (
    AgentPersona,
    AgentRun,
    AgentStepName,
    StepRecord,
)
from app.domain.entities.user import User
from app.domain.repositories.agent_run_repository import IAgentRunRepository
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.infrastructure.llm.prompts import (
    CODE_ENGINEERING_SYSTEM_PROMPT,
    DASHBOARD_BI_SYSTEM_PROMPT,
    DATA_ANALYST_SYSTEM_PROMPT,
    NL_TO_SQL_SYSTEM_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    format_schema_context,
)
from app.infrastructure.llm.provider_service import LLMProviderService

logger = get_logger(__name__)

# Simple heuristic patterns for prompt injection detection
_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard the above",
    "forget your instructions",
    "you are now",
    "new instructions:",
    "system prompt:",
    "override:",
]

_SECRET_PATTERNS = [
    re.compile(r"postgres(?:ql)?://[^\s:]+:[^\s@]+@[^\s]+", re.IGNORECASE),
    re.compile(
        r"(password|secret|token|api_key|credentials)\s*=\s*['\"][^'\"]+['\"]",
        re.IGNORECASE,
    ),
    re.compile(
        r"(password|secret|token|api_key|credentials)\s*=\s*[^\s,]+",
        re.IGNORECASE,
    ),
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
]


def _check_prompt_injection(text: str) -> bool:
    """Check if user text contains suspected prompt injection patterns."""
    lowered = text.lower()
    return any(pattern in lowered for pattern in _INJECTION_PATTERNS)


def _sanitize_error_message(text: str) -> str:
    """Sanitize exception text to prevent leaking connection strings or credentials."""
    if not text:
        return text
    sanitized = text
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized[:200]


class ExecuteAgentQueryUseCase:
    """Application use case for executing an NL→SQL agent pipeline.

    Coordinates schema resolution, LLM invocation, SQL validation,
    query execution, and run persistence. All operations go through
    existing NexusBI services — the agent never gets raw DB access.

    Parameters
    ----------
    llm_service : LLMProviderService
        LLM provider service with failover.
    query_service : QueryService
        Existing universal query engine.
    dataset_repository : IDatasetRepository
        Dataset persistence port.
    agent_run_repository : IAgentRunRepository
        Agent run persistence port.
    audit_logger : AuditLogger
        Structured audit logger.
    authorization_service : IAuthorizationService | None
        Optional authorization service for RBAC enforcement.
    tool_registry : AgentToolRegistry | None
        Optional agent tool registry for executing safe allowlisted tools.
    """

    def __init__(
        self,
        *,
        llm_service: LLMProviderService,
        query_service: QueryService,
        dataset_repository: IDatasetRepository,
        agent_run_repository: IAgentRunRepository,
        audit_logger: AuditLogger,
        authorization_service: IAuthorizationService | None = None,
        tool_registry: AgentToolRegistry | None = None,
        visualization_service: Any | None = None,
    ) -> None:
        self._llm = llm_service
        self._query = query_service
        self._dataset_repo = dataset_repository
        self._run_repo = agent_run_repository
        self._audit = audit_logger
        self._auth_service = authorization_service
        self._tool_registry = tool_registry
        if visualization_service is None:
            from app.application.services.visualization_service import (
                VisualizationService,
            )

            self._viz_service = VisualizationService()
        else:
            self._viz_service = visualization_service

    def execute(
        self,
        *,
        user: User,
        natural_language_query: str,
        dataset_id: str | None = None,
        workspace_id: str | None = None,
        agent_role: str = "sql_data",
    ) -> AgentRun:
        """Execute the full agent pipeline with specialist persona support.

        Parameters
        ----------
        user : User
            The authenticated user initiating the query.
        natural_language_query : str
            The user's natural language question.
        dataset_id : str | None
            The target dataset to query against (optional for tool queries).
        workspace_id : str | None
            Optional workspace scope.
        agent_role : str
            Specialist agent persona (sql_data, data_analyst, dashboard_bi,
            code_engineering, orchestrator).

        Returns
        -------
        AgentRun
            The completed (or failed) agent run entity.

        Raises
        ------
        ValidationError
            If the query text is too short or persona role is invalid.
        PromptInjectionError
            If the query contains suspected injection patterns.
        AuthorizationError
            If user lacks datasets:read permission or violates workspace boundaries.
        EntityNotFoundError
            If the dataset does not exist.
        """
        # --- Input validation ---
        trimmed_query = natural_language_query.strip()
        if len(trimmed_query) < 3:
            raise ValidationError(
                message="Query text too short",
                detail=(
                    "Natural language query must be at least 3 non-whitespace "
                    "characters."
                ),
            )

        # --- Persona validation ---
        valid_personas = {p.value for p in AgentPersona}
        if agent_role not in valid_personas:
            raise ValidationError(
                message="Invalid agent persona role",
                detail=f"Role '{agent_role}' is not a valid specialist persona.",
            )

        # --- Pre-flight: injection check ---
        if _check_prompt_injection(natural_language_query):
            self._audit.log_security_event(
                event_type="prompt_injection_detected",
                user_id=user.id,
                detail=f"Blocked NL query: {natural_language_query[:100]}...",
                severity="warning",
            )
            raise PromptInjectionError(
                detail="The query was rejected by the security filter."
            )

        # --- Tool invocation intent check ---
        query_lower = trimmed_query.lower()
        is_org_keyword = (
            "organization" in query_lower
            or "organisations" in query_lower
            or "orgs" in query_lower
        )

        # Distinguish simple lookups from analytical requests:
        # Simple: "show/list/what/which/where organizations"
        # Analytical: "how many/analyze/compare/insight/trend organizations"
        _ANALYTICAL_MARKERS = (
            "how many",
            "how much",
            "analyze",
            "analyse",
            "compare",
            "insight",
            "statistics",
            "summary",
            "trend",
            "breakdown",
            "distribution",
            "count",
            "active",
            "inactive",
            "total",
            "percentage",
            "ratio",
            "growth",
        )
        _LOOKUP_MARKERS = (
            "show",
            "list",
            "what",
            "which",
            "where",
            "display",
            "get",
            "fetch",
            "find",
        )
        is_analytical_org = is_org_keyword and any(
            m in query_lower for m in _ANALYTICAL_MARKERS
        )
        is_simple_org_lookup = (
            is_org_keyword
            and any(m in query_lower for m in _LOOKUP_MARKERS)
            and not is_analytical_org
        )

        # Simple org lookups go through deterministic tool shortcut
        if is_simple_org_lookup:
            # Execute tool list_organizations via tool_registry
            run = AgentRun(
                id=str(uuid.uuid4()),
                user_id=user.id,
                dataset_id=dataset_id,
                natural_language_query=natural_language_query,
                workspace_id=workspace_id,
                agent_role=agent_role,
            )
            run.mark_running()
            run = self._run_repo.save(run)

            try:
                if self._tool_registry is None:
                    raise ValidationError(
                        message="Tool registry unavailable",
                        detail="AgentToolRegistry is not configured",
                    )

                tool_kwargs = {}
                if workspace_id:
                    tool_kwargs["workspace_id"] = workspace_id

                tool_result = self._tool_registry.execute_tool(
                    "list_organizations", user=user, kwargs=tool_kwargs
                )

                step = StepRecord(step_name=AgentStepName.QUERY_EXECUTE)
                step.status = "success"
                step.completed_at = datetime.now(UTC)
                step.latency_ms = 10.0
                items = tool_result.get("items", [])
                step.output_summary = f"Retrieved {len(items)} organizations"
                run.add_step(step)

                org_count = tool_result.get("total", 0)
                org_lines = [
                    f"- {o.get('name')} ({o.get('slug')})"
                    for o in items
                    if isinstance(o, dict) and o.get("name")
                ]
                insights = (
                    f"Found {org_count} organization(s):\n" + "\n".join(org_lines)
                    if org_lines
                    else f"Found {org_count} organization(s)."
                )

                run.insights = insights
                run.mark_completed(
                    generated_sql="TOOL: list_organizations", confidence=1.0
                )
                run = self._run_repo.save(run)

                self._audit.log_query_execution(
                    user_id=user.id,
                    query_text=natural_language_query,
                    generated_sql="TOOL: list_organizations",
                    execution_time_ms=sum(s.latency_ms for s in run.steps),
                    row_count=org_count,
                    tables_accessed=["organizations"],
                    status="success",
                )
                return run
            except NexusBIError as nbi_err:
                sanitized_err = _sanitize_error_message(
                    nbi_err.detail or nbi_err.message
                )
                run.mark_failed(error=sanitized_err)
                self._run_repo.save(run)
                raise

        # Analytical org queries (and all non-org queries without dataset_id)
        # fall through to the full LLM pipeline below.
        # For analytical org queries without a dataset_id, discover one.
        if is_analytical_org and dataset_id is None:
            from app.domain.value_objects.filter_params import FilterParams

            discovered_datasets, _ = self._dataset_repo.list(
                FilterParams(page=1, page_size=20, is_active=True)
            )
            if workspace_id:
                discovered_datasets = [
                    d
                    for d in discovered_datasets
                    if not getattr(d, "workspace_id", None)
                    or d.workspace_id == workspace_id
                ]

            if discovered_datasets:
                dataset_id = discovered_datasets[0].id

        # Generic dataset auto-discovery when dataset_id is not provided
        if dataset_id is None:
            from app.domain.value_objects.filter_params import FilterParams

            discovered_datasets, _ = self._dataset_repo.list(
                FilterParams(page=1, page_size=20, is_active=True)
            )
            if workspace_id:
                discovered_datasets = [
                    d
                    for d in discovered_datasets
                    if not getattr(d, "workspace_id", None)
                    or d.workspace_id == workspace_id
                ]

            if not discovered_datasets:
                raise ValidationError(
                    message="Dataset ID required",
                    detail="dataset_id parameter is required for SQL data queries.",
                )

            dataset_id = discovered_datasets[0].id

        # --- RBAC permission check for datasets:read ---
        if self._auth_service and not self._auth_service.has_permission(
            user, "datasets:read"
        ):
            raise AuthorizationError(
                message="Permission denied",
                detail=(
                    "User lacks datasets:read permission required for dataset "
                    "query execution."
                ),
            )

        # --- Multi-tenant isolation check ---
        dataset = self._dataset_repo.get_by_id(dataset_id)
        if dataset is None:
            raise EntityNotFoundError("Dataset", dataset_id)

        dataset_ws = getattr(dataset, "workspace_id", None)
        if workspace_id and dataset_ws and dataset_ws != workspace_id:
            raise AuthorizationError(
                message="Permission denied",
                detail="Dataset does not belong to the requested workspace scope",
            )

        # --- Initialize AgentRun ---
        run = AgentRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            dataset_id=dataset_id,
            natural_language_query=natural_language_query,
            workspace_id=workspace_id,
            agent_role=agent_role,
        )
        run.mark_running()
        run = self._run_repo.save(run)

        try:
            # Step 1: Resolve schema
            schema_context = self._step_schema_resolve(run, dataset_id)

            # Step 2: Generate SQL via LLM
            generated_sql, confidence, llm_response = self._step_sql_generate(
                run, natural_language_query, schema_context, user.id
            )

            # Step 3: Validate SQL via existing QueryService
            self._step_sql_validate(run, generated_sql)

            # Step 4: Execute SQL via existing QueryService
            query_result = self._step_query_execute(run, generated_sql, dataset_id)

            # Step 5: Execute specialist persona logic if requested
            self._step_persona_execute(
                run=run,
                user_id=user.id,
                agent_role=agent_role,
                schema_context=schema_context,
                nl_query=natural_language_query,
                generated_sql=generated_sql,
                query_result=query_result,
            )

            # Mark completed
            run.mark_completed(generated_sql=generated_sql, confidence=confidence)
            run = self._run_repo.save(run)

            # Audit the successful run
            self._audit.log_query_execution(
                user_id=user.id,
                query_text=natural_language_query,
                generated_sql=generated_sql,
                execution_time_ms=sum(s.latency_ms for s in run.steps),
                row_count=query_result.row_count if query_result else 0,
                tables_accessed=[dataset_id],
                status="success",
            )

            return run

        except NexusBIError:
            # Re-raise known NexusBI errors after recording sanitized failure
            sanitized_err = _sanitize_error_message(run.error or "Pipeline step failed")
            run.mark_failed(error=sanitized_err)
            self._run_repo.save(run)
            raise

        except Exception as exc:
            # Unexpected error — record sanitized error and re-raise
            clean_error = _sanitize_error_message(f"{type(exc).__name__}: {exc}")
            run.mark_failed(error=f"Unexpected error: {clean_error}")
            self._run_repo.save(run)
            logger.exception("Agent pipeline unexpected error", run_id=run.id)
            raise

    def _step_schema_resolve(self, run: AgentRun, dataset_id: str) -> str:
        """Step 1: Resolve dataset schema to prompt context."""
        step = StepRecord(step_name=AgentStepName.SCHEMA_RESOLVE)
        start = time.monotonic()

        try:
            dataset = self._dataset_repo.get_by_id(dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dataset_id)

            # Extract schema metadata from dataset
            schema_meta = getattr(dataset, "schema_metadata", {}) or {}
            columns: list[dict[str, str]] = schema_meta.get("columns", [])

            # If no column metadata, create a minimal context
            if not columns:
                table_name = getattr(dataset, "object_name", None) or getattr(
                    dataset, "name", "unknown_table"
                )
                schema_context = (
                    f'Table: "{table_name}"\n'
                    "Columns: (schema metadata not available — "
                    "generate a broad SELECT *)"
                )
            else:
                table_name = str(
                    getattr(dataset, "object_name", None)
                    or getattr(dataset, "name", None)
                    or "unknown_table"
                )
                # Limit to 50 columns to control context budget
                truncated_columns = columns[:50]
                schema_context = format_schema_context(table_name, truncated_columns)

            elapsed = (time.monotonic() - start) * 1000
            step.status = "success"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.output_summary = f"Resolved {len(columns)} columns for {table_name}"
            run.add_step(step)

            return schema_context

        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            step.status = "error"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.error = _sanitize_error_message(str(exc))
            run.add_step(step)
            run.mark_failed(error=f"Schema resolution failed: {step.error}")
            raise

    def _step_sql_generate(
        self,
        run: AgentRun,
        nl_query: str,
        schema_context: str,
        user_id: str,
    ) -> tuple[str, float, LLMResponse]:
        """Step 2: Generate SQL from natural language via LLM."""
        step = StepRecord(step_name=AgentStepName.SQL_GENERATE)
        start = time.monotonic()

        try:
            system_prompt = NL_TO_SQL_SYSTEM_PROMPT.format(
                schema_context=schema_context
            )

            response = self._llm.complete(
                system_prompt=system_prompt,
                user_message=nl_query,
                user_id=user_id,
            )

            generated_sql = response.content.strip()
            # Remove markdown code fences if LLM wraps output
            if generated_sql.startswith("```"):
                lines = generated_sql.split("\n")
                # Remove first and last lines (``` markers)
                generated_sql = "\n".join(
                    line for line in lines[1:] if not line.strip().startswith("```")
                ).strip()

            # Accumulate cost
            run.accumulate_cost(
                tokens=response.total_tokens,
                cost_usd=response.cost_usd or 0.0,
            )

            # Estimate confidence based on response metadata
            confidence = 0.85  # Default confidence for clean generation
            stop_reason = response.metadata.get("stop_reason")
            if stop_reason == "max_tokens":
                confidence = 0.4  # Truncated output — low confidence

            elapsed = (time.monotonic() - start) * 1000
            step.status = "success"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.output_summary = f"Generated SQL ({len(generated_sql)} chars)"
            step.metadata = {
                "model": response.model,
                "tokens": response.total_tokens,
                "confidence": confidence,
            }
            run.add_step(step)

            return generated_sql, confidence, response

        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            step.status = "error"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.error = _sanitize_error_message(str(exc))
            run.add_step(step)
            run.mark_failed(error=f"SQL generation failed: {step.error}")
            raise

    def _step_sql_validate(self, run: AgentRun, generated_sql: str) -> None:
        """Step 3: Validate generated SQL via existing QueryService."""
        step = StepRecord(step_name=AgentStepName.SQL_VALIDATE)
        start = time.monotonic()

        try:
            from app.domain.value_objects.query import QueryRequest

            request = QueryRequest.create(sql=generated_sql)
            self._query.validate(request)

            elapsed = (time.monotonic() - start) * 1000
            step.status = "success"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.output_summary = "SQL passed validation"
            run.add_step(step)

        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            step.status = "error"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.error = _sanitize_error_message(str(exc))
            run.add_step(step)
            run.mark_failed(error=f"SQL validation failed: {step.error}")
            raise

    def _step_query_execute(
        self, run: AgentRun, generated_sql: str, dataset_id: str
    ) -> Any:
        """Step 4: Execute validated SQL via existing QueryService."""
        step = StepRecord(step_name=AgentStepName.QUERY_EXECUTE)
        start = time.monotonic()

        try:
            from app.domain.value_objects.query import QueryRequest

            request = QueryRequest.create(
                sql=generated_sql,
                limit=100,  # Safety limit for agent-generated queries
                dataset_id=dataset_id,
            )
            result = self._query.execute(request)

            run.query_result = {
                "rows": result.rows,
                "columns": [
                    c.name if hasattr(c, "name") else str(c) for c in result.columns
                ],
                "column_types": result.column_types,
                "row_count": result.row_count,
                "execution_time_ms": result.execution_time * 1000,
                "truncated": False,
            }

            elapsed = (time.monotonic() - start) * 1000
            step.status = "success"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.output_summary = f"Returned {result.row_count} rows"
            run.add_step(step)

            return result

        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            step.status = "error"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.error = _sanitize_error_message(str(exc))
            run.add_step(step)
            run.mark_failed(error=f"Query execution failed: {step.error}")
            raise

    def _step_persona_execute(
        self,
        *,
        run: AgentRun,
        user_id: str,
        agent_role: str,
        schema_context: str,
        nl_query: str,
        generated_sql: str,
        query_result: Any,
    ) -> None:
        """Step 5: Execute specialist persona logic based on agent_role."""
        if agent_role in (AgentPersona.SQL_DATA, "sql_data"):
            return

        step = StepRecord(step_name=AgentStepName.PERSONA_EXECUTE)
        start = time.monotonic()

        try:
            sample_rows = getattr(query_result, "rows", [])[:10] if query_result else []
            columns = getattr(query_result, "columns", []) if query_result else []
            row_count = getattr(query_result, "row_count", 0) if query_result else 0

            if agent_role in (AgentPersona.DATA_ANALYST, "data_analyst"):
                prompt = DATA_ANALYST_SYSTEM_PROMPT.format(
                    schema_context=schema_context,
                    generated_sql=generated_sql,
                    row_count=row_count,
                    results_sample=str(sample_rows),
                )
                response = self._llm.complete(
                    system_prompt=prompt,
                    user_message=nl_query,
                    user_id=user_id,
                )
                run.insights = response.content.strip()
                run.accumulate_cost(response.total_tokens, response.cost_usd or 0.0)

                # Produce structured chart spec if query benefits from visualization
                if query_result and self._viz_service.should_visualize(
                    nl_query, query_result
                ):
                    try:
                        run.visualization_config = (
                            self._viz_service.generate_chart_specification(
                                natural_language_query=nl_query,
                                query_result=query_result,
                            )
                        )
                    except Exception as viz_err:
                        logger.warning(
                            "Data analyst visualization spec warning: %s", viz_err
                        )

            elif agent_role in (AgentPersona.DASHBOARD_BI, "dashboard_bi"):
                if query_result and getattr(query_result, "rows", None):
                    try:
                        run.visualization_config = (
                            self._viz_service.generate_chart_specification(
                                natural_language_query=nl_query,
                                query_result=query_result,
                            )
                        )
                    except Exception as viz_err:
                        logger.warning("Dashboard BI visualization error: %s", viz_err)
                if not run.visualization_config:
                    prompt = DASHBOARD_BI_SYSTEM_PROMPT.format(
                        schema_context=schema_context,
                        generated_sql=generated_sql,
                        columns=str(columns),
                    )
                    response = self._llm.complete(
                        system_prompt=prompt,
                        user_message=nl_query,
                        user_id=user_id,
                    )
                    run.accumulate_cost(response.total_tokens, response.cost_usd or 0.0)
                    run.visualization_config = {
                        "type": "bar",
                        "title": "Query Result Visualization",
                        "summary": response.content.strip()[:200],
                    }
                v_type = run.visualization_config.get("type", "chart")
                v_title = run.visualization_config.get("title", "Chart")
                run.insights = f"Generated {v_type} specification: {v_title}"

            elif agent_role in (AgentPersona.CODE_ENGINEERING, "code_engineering"):
                prompt = CODE_ENGINEERING_SYSTEM_PROMPT.format(
                    schema_context=schema_context,
                    natural_language_query=nl_query,
                )
                response = self._llm.complete(
                    system_prompt=prompt,
                    user_message=nl_query,
                    user_id=user_id,
                )
                run.code_snippet = response.content.strip()
                run.accumulate_cost(response.total_tokens, response.cost_usd or 0.0)

            elif agent_role in (AgentPersona.ORCHESTRATOR, "orchestrator"):
                analyst_prompt = DATA_ANALYST_SYSTEM_PROMPT.format(
                    schema_context=schema_context,
                    generated_sql=generated_sql,
                    row_count=row_count,
                    results_sample=str(sample_rows),
                )
                analyst_resp = self._llm.complete(
                    system_prompt=analyst_prompt,
                    user_message=nl_query,
                    user_id=user_id,
                )
                run.accumulate_cost(
                    analyst_resp.total_tokens, analyst_resp.cost_usd or 0.0
                )
                insights_text = analyst_resp.content.strip()

                if query_result and self._viz_service.should_visualize(
                    nl_query, query_result
                ):
                    try:
                        run.visualization_config = (
                            self._viz_service.generate_chart_specification(
                                natural_language_query=nl_query,
                                query_result=query_result,
                            )
                        )
                    except Exception as viz_err:
                        logger.warning(
                            "Orchestrator visualization spec warning: %s", viz_err
                        )

                orch_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(
                    natural_language_query=nl_query,
                    generated_sql=generated_sql,
                    data_insights=insights_text,
                    visualization_summary=str(
                        run.visualization_config or "No visualization generated"
                    ),
                )
                orch_resp = self._llm.complete(
                    system_prompt=orch_prompt,
                    user_message=nl_query,
                    user_id=user_id,
                )
                run.accumulate_cost(orch_resp.total_tokens, orch_resp.cost_usd or 0.0)
                run.insights = orch_resp.content.strip()

            elapsed = (time.monotonic() - start) * 1000
            step.status = "success"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.output_summary = f"Executed {agent_role} persona"
            run.add_step(step)

        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            step.status = "error"
            step.completed_at = datetime.now(UTC)
            step.latency_ms = elapsed
            step.error = _sanitize_error_message(str(exc))
            run.add_step(step)
            logger.warning(f"Persona execution {agent_role} step warning: {exc}")
