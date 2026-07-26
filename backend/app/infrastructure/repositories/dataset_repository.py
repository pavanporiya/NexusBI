"""SQLAlchemy implementation of the Dataset repository.

Fulfills the IDatasetRepository Protocol contract defined in the domain layer.
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.entities.dataset import Dataset
from app.domain.value_objects.filter_params import FilterParams
from app.infrastructure.database.models import DatasetModel
from app.infrastructure.mappers.dataset_mapper import DatasetMapper


class SQLAlchemyDatasetRepository:
    """Concrete IDatasetRepository backed by SQLAlchemy.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, dataset_id: str) -> Dataset | None:
        """Fetch a Dataset by its unique ID."""
        stmt = select(DatasetModel).where(DatasetModel.id == dataset_id)
        model = self._session.execute(stmt).scalars().first()
        return DatasetMapper.to_domain(model) if model else None

    def save(self, dataset: Dataset) -> Dataset:
        """Persist a new Dataset or update an existing one."""
        existing = self._session.get(DatasetModel, dataset.id)
        if existing:
            DatasetMapper.update_model(existing, dataset)
            model = existing
        else:
            model = DatasetMapper.to_model(dataset)
            self._session.add(model)

        self._session.flush()
        self._session.refresh(model)
        return DatasetMapper.to_domain(model)

    def delete(self, dataset_id: str) -> bool:
        """Permanently remove a Dataset by ID."""
        model = self._session.get(DatasetModel, dataset_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list(self, params: FilterParams) -> tuple[list[Dataset], int]:
        """Fetch a paginated, filtered, sorted, and searched list of Datasets."""
        stmt = select(DatasetModel)

        # 1. Filtering
        if params.name:
            stmt = stmt.where(DatasetModel.name.ilike(f"%{params.name}%"))
        if params.owner_id:
            stmt = stmt.where(DatasetModel.owner_id == params.owner_id)
        if params.created_at_from:
            stmt = stmt.where(DatasetModel.created_at >= params.created_at_from)
        if params.created_at_to:
            stmt = stmt.where(DatasetModel.created_at <= params.created_at_to)
        if params.updated_at_from:
            stmt = stmt.where(DatasetModel.updated_at >= params.updated_at_from)
        if params.updated_at_to:
            stmt = stmt.where(DatasetModel.updated_at <= params.updated_at_to)
        if params.is_active is not None:
            stmt = stmt.where(DatasetModel.is_active == params.is_active)

        # 2. Keyword Search
        if params.search:
            pattern = f"%{params.search}%"
            stmt = stmt.where(
                or_(
                    DatasetModel.name.ilike(pattern),
                    DatasetModel.description.ilike(pattern),
                    DatasetModel.query_or_table.ilike(pattern),
                )
            )

        # 3. Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self._session.execute(count_stmt).scalar() or 0

        # 4. Sorting
        sort_column = getattr(DatasetModel, params.sort_by, DatasetModel.created_at)
        if params.sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())

        # 5. Pagination
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        models = self._session.execute(stmt).scalars().all()
        return [DatasetMapper.to_domain(m) for m in models], total
