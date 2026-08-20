"""Agent run repository interface.

Defines the persistence port for AgentRun domain entities,
following the existing IXxxRepository pattern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.agent_run import AgentRun


class IAgentRunRepository(ABC):
    """Port interface for AgentRun persistence operations."""

    @abstractmethod
    def save(self, agent_run: AgentRun) -> AgentRun:
        """Persist a new or updated AgentRun entity.

        Parameters
        ----------
        agent_run : AgentRun
            The domain entity to persist.

        Returns
        -------
        AgentRun
            The persisted entity.
        """

    @abstractmethod
    def get_by_id(self, run_id: str) -> AgentRun | None:
        """Retrieve an AgentRun by its unique ID.

        Parameters
        ----------
        run_id : str
            The run's unique identifier.

        Returns
        -------
        AgentRun | None
            The entity if found, None otherwise.
        """

    @abstractmethod
    def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AgentRun]:
        """List agent runs for a specific user, ordered by creation time.

        Parameters
        ----------
        user_id : str
            The user's unique identifier.
        limit : int
            Maximum number of runs to return.
        offset : int
            Number of runs to skip.

        Returns
        -------
        list[AgentRun]
            Ordered list of the user's agent runs.
        """
