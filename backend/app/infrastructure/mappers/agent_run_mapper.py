"""AgentRun entity ↔ ORM model mapper."""

from __future__ import annotations

from typing import Any

from app.domain.entities.agent_run import AgentRun, AgentRunStatus, StepRecord
from app.infrastructure.database.models import AgentRunModel


class AgentRunMapper:
    """Mapper between AgentRun domain entities and AgentRunModel ORM objects."""

    @staticmethod
    def to_domain(model: AgentRunModel) -> AgentRun:
        """Convert an AgentRunModel ORM instance to an AgentRun domain entity."""
        steps_raw: list[dict[str, Any]] = model.steps_json or []
        steps = [
            StepRecord(
                step_name=s.get("step_name", ""),
                status=s.get("status", "unknown"),
                started_at=s.get("started_at", model.created_at),
                completed_at=s.get("completed_at"),
                latency_ms=s.get("latency_ms", 0.0),
                input_summary=s.get("input_summary", ""),
                output_summary=s.get("output_summary", ""),
                error=s.get("error"),
                metadata=s.get("metadata", {}),
            )
            for s in steps_raw
        ]

        return AgentRun(
            id=model.id,
            user_id=model.user_id,
            dataset_id=model.dataset_id,
            natural_language_query=model.natural_language_query,
            organization_id=model.organization_id,
            workspace_id=model.workspace_id,
            agent_role=getattr(model, "agent_role", None) or "sql_data",
            generated_sql=model.generated_sql,
            insights=getattr(model, "insights", None),
            visualization_config=(
                getattr(model, "visualization_config_json", None) or {}
            ),
            code_snippet=getattr(model, "code_snippet", None),
            query_result=getattr(model, "query_result_json", None),
            status=AgentRunStatus(model.status),
            confidence=model.confidence,
            steps=steps,
            total_tokens=model.total_tokens,
            total_cost_usd=model.total_cost_usd,
            error=model.error,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: AgentRun) -> AgentRunModel:
        """Convert an AgentRun domain entity to a new AgentRunModel ORM instance."""
        return AgentRunModel(
            id=entity.id,
            user_id=entity.user_id,
            dataset_id=entity.dataset_id,
            natural_language_query=entity.natural_language_query,
            organization_id=entity.organization_id,
            workspace_id=entity.workspace_id,
            agent_role=entity.agent_role,
            generated_sql=entity.generated_sql,
            insights=entity.insights,
            visualization_config_json=entity.visualization_config,
            code_snippet=entity.code_snippet,
            query_result_json=entity.query_result,
            status=entity.status.value,
            confidence=entity.confidence,
            steps_json=AgentRunMapper._steps_to_json(entity.steps),
            total_tokens=entity.total_tokens,
            total_cost_usd=entity.total_cost_usd,
            error=entity.error,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: AgentRunModel, entity: AgentRun) -> None:
        """Update an existing AgentRunModel from an AgentRun entity."""
        model.agent_role = entity.agent_role
        model.generated_sql = entity.generated_sql
        model.insights = entity.insights
        model.visualization_config_json = entity.visualization_config
        model.code_snippet = entity.code_snippet
        model.query_result_json = entity.query_result
        model.status = entity.status.value
        model.confidence = entity.confidence
        model.steps_json = AgentRunMapper._steps_to_json(entity.steps)
        model.total_tokens = entity.total_tokens
        model.total_cost_usd = entity.total_cost_usd
        model.error = entity.error
        model.updated_at = entity.updated_at

    @staticmethod
    def _steps_to_json(steps: list[StepRecord]) -> list[dict[str, Any]]:
        """Serialise StepRecord list to JSON-compatible dicts."""
        result: list[dict[str, Any]] = []
        for s in steps:
            record: dict[str, Any] = {
                "step_name": s.step_name,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "latency_ms": s.latency_ms,
                "input_summary": s.input_summary,
                "output_summary": s.output_summary,
                "error": s.error,
                "metadata": s.metadata,
            }
            result.append(record)
        return result
