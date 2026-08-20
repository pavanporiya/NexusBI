"""SQLAlchemy implementation of the AgentRun repository.

Fulfills the IAgentRunRepository contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.agent_run import AgentRun
from app.domain.repositories.agent_run_repository import IAgentRunRepository
from app.infrastructure.database.models import AgentRunModel
from app.infrastructure.mappers.agent_run_mapper import AgentRunMapper


class SQLAlchemyAgentRunRepository(IAgentRunRepository):
    """Concrete IAgentRunRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, agent_run: AgentRun) -> AgentRun:
        """Persist a new AgentRun or update an existing one."""
        existing = self._session.get(AgentRunModel, agent_run.id)
        if existing:
            AgentRunMapper.update_model(existing, agent_run)
            model = existing
        else:
            model = AgentRunMapper.to_model(agent_run)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return AgentRunMapper.to_domain(model)

    def get_by_id(self, run_id: str) -> AgentRun | None:
        """Fetch an AgentRun by its unique ID."""
        stmt = select(AgentRunModel).where(AgentRunModel.id == run_id)
        model = self._session.execute(stmt).scalars().first()
        return AgentRunMapper.to_domain(model) if model else None

    def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AgentRun]:
        """List agent runs for a specific user, ordered by creation time desc."""
        stmt = (
            select(AgentRunModel)
            .where(AgentRunModel.user_id == user_id)
            .order_by(AgentRunModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        models = self._session.execute(stmt).scalars().all()
        return [AgentRunMapper.to_domain(m) for m in models]
