"""Get Agent Run use case.

Retrieves agent run details or lists user's run history.
"""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.domain.entities.agent_run import AgentRun
from app.domain.repositories.agent_run_repository import IAgentRunRepository


class GetAgentRunUseCase:
    """Use case for retrieving a specific agent run."""

    def __init__(self, agent_run_repository: IAgentRunRepository) -> None:
        self._repo = agent_run_repository

    def execute(self, run_id: str, user_id: str) -> AgentRun:
        """Fetch an AgentRun by ID and verify user ownership."""
        run = self._repo.get_by_id(run_id)
        if run is None or run.user_id != user_id:
            raise EntityNotFoundError("AgentRun", run_id)
        return run


class ListAgentRunsUseCase:
    """Use case for listing user's agent runs."""

    def __init__(self, agent_run_repository: IAgentRunRepository) -> None:
        self._repo = agent_run_repository

    def execute(self, user_id: str, limit: int = 20, offset: int = 0) -> list[AgentRun]:
        """Fetch paginated list of agent runs for user."""
        return self._repo.list_by_user(user_id, limit=limit, offset=offset)
