"""SQLAlchemy implementation of the Report repository.

Fulfills the IReportRepository Protocol contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.entities.report import Report
from app.domain.value_objects.filter_params import FilterParams
from app.infrastructure.database.models import ReportModel
from app.infrastructure.mappers.report_mapper import ReportMapper


class SQLAlchemyReportRepository:
    """Concrete IReportRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, report_id: str) -> Report | None:
        """Fetch a Report by its unique ID."""
        stmt = select(ReportModel).where(ReportModel.id == report_id)
        model = self._session.execute(stmt).scalars().first()
        return ReportMapper.to_domain(model) if model else None

    def save(self, report: Report) -> Report:
        """Persist a new Report or update an existing one."""
        existing = self._session.get(ReportModel, report.id)
        if existing:
            ReportMapper.update_model(existing, report)
            model = existing
        else:
            model = ReportMapper.to_model(report)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return ReportMapper.to_domain(model)

    def delete(self, report_id: str) -> bool:
        """Permanently remove a Report by ID."""
        model = self._session.get(ReportModel, report_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list(self, params: FilterParams) -> tuple[list[Report], int]:
        """Fetch a paginated, filtered, sorted, and searched list of Reports."""
        stmt = select(ReportModel)

        # 1. Filtering
        if params.name:
            stmt = stmt.where(ReportModel.name.ilike(f"%{params.name}%"))
        if params.owner_id:
            stmt = stmt.where(ReportModel.owner_id == params.owner_id)
        if params.dataset_id:
            stmt = stmt.where(ReportModel.dataset_id == params.dataset_id)
        if params.report_type:
            stmt = stmt.where(ReportModel.report_type == params.report_type.lower())
        if params.is_active is not None:
            stmt = stmt.where(ReportModel.is_active == params.is_active)
        if params.created_at_from:
            stmt = stmt.where(ReportModel.created_at >= params.created_at_from)
        if params.created_at_to:
            stmt = stmt.where(ReportModel.created_at <= params.created_at_to)
        if params.updated_at_from:
            stmt = stmt.where(ReportModel.updated_at >= params.updated_at_from)
        if params.updated_at_to:
            stmt = stmt.where(ReportModel.updated_at <= params.updated_at_to)

        # 2. Keyword Search
        if params.search:
            pattern = f"%{params.search}%"
            stmt = stmt.where(
                or_(
                    ReportModel.name.ilike(pattern),
                    ReportModel.description.ilike(pattern),
                    ReportModel.report_type.ilike(pattern),
                    ReportModel.output_format.ilike(pattern),
                    ReportModel.query.ilike(pattern),
                )
            )

        # 3. Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self._session.execute(count_stmt).scalar() or 0

        # 4. Sorting
        sort_column = getattr(ReportModel, params.sort_by, ReportModel.created_at)
        if params.sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())

        # 5. Pagination
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        models = self._session.execute(stmt).scalars().all()
        return [ReportMapper.to_domain(m) for m in models], total
