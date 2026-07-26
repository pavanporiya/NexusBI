"""SQLAlchemy implementation of the Dashboard repository.

Fulfills the IDashboardRepository Protocol contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.entities.dashboard import Dashboard
from app.domain.value_objects.filter_params import FilterParams
from app.infrastructure.database.models import DashboardModel
from app.infrastructure.mappers.dashboard_mapper import DashboardMapper


class SQLAlchemyDashboardRepository:
    """Concrete IDashboardRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, dashboard_id: str) -> Dashboard | None:
        """Fetch a Dashboard by its unique ID."""
        stmt = select(DashboardModel).where(DashboardModel.id == dashboard_id)
        model = self._session.execute(stmt).scalars().first()
        return DashboardMapper.to_domain(model) if model else None

    def save(self, dashboard: Dashboard) -> Dashboard:
        """Persist a new Dashboard or update an existing one."""
        existing = self._session.get(DashboardModel, dashboard.id)
        if existing:
            DashboardMapper.update_model(existing, dashboard)
            model = existing
        else:
            model = DashboardMapper.to_model(dashboard)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return DashboardMapper.to_domain(model)

    def delete(self, dashboard_id: str) -> bool:
        """Permanently remove a Dashboard by ID."""
        model = self._session.get(DashboardModel, dashboard_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list(self, params: FilterParams) -> tuple[list[Dashboard], int]:
        """Fetch a paginated, filtered, sorted, and searched list of Dashboards."""
        stmt = select(DashboardModel)

        # 1. Filtering
        if params.name:
            stmt = stmt.where(DashboardModel.name.ilike(f"%{params.name}%"))
        if params.owner_id:
            stmt = stmt.where(DashboardModel.owner_id == params.owner_id)
        if params.dataset_id:
            stmt = stmt.where(DashboardModel.dataset_id == params.dataset_id)
        if params.is_active is not None:
            stmt = stmt.where(DashboardModel.is_active == params.is_active)
        if params.is_public is not None:
            stmt = stmt.where(DashboardModel.is_public == params.is_public)
        if params.created_at_from:
            stmt = stmt.where(DashboardModel.created_at >= params.created_at_from)
        if params.created_at_to:
            stmt = stmt.where(DashboardModel.created_at <= params.created_at_to)
        if params.updated_at_from:
            stmt = stmt.where(DashboardModel.updated_at >= params.updated_at_from)
        if params.updated_at_to:
            stmt = stmt.where(DashboardModel.updated_at <= params.updated_at_to)

        # 2. Keyword Search
        if params.search:
            pattern = f"%{params.search}%"
            stmt = stmt.where(
                or_(
                    DashboardModel.name.ilike(pattern),
                    DashboardModel.description.ilike(pattern),
                )
            )

        # 3. Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self._session.execute(count_stmt).scalar() or 0

        # 4. Sorting
        sort_column = getattr(DashboardModel, params.sort_by, DashboardModel.created_at)
        if params.sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())

        # 5. Pagination
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        models = self._session.execute(stmt).scalars().all()
        return [DashboardMapper.to_domain(m) for m in models], total
