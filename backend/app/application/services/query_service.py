"""Query application service orchestrating validation, planning, execution."""

from __future__ import annotations

from typing import Any

from app.application.interfaces.i_query_executor import IQueryExecutor
from app.application.interfaces.i_query_planner import IQueryPlanner
from app.application.interfaces.i_query_validator import IQueryValidator
from app.core.exceptions import EntityNotFoundError
from app.domain.enums import DatasetObjectType
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.value_objects.query import QueryMetadata, QueryRequest, QueryResult


class QueryService:
    """Application service for the Universal Query Engine."""

    def __init__(
        self,
        validator: IQueryValidator,
        executor: IQueryExecutor,
        planner: IQueryPlanner,
        dataset_repository: IDatasetRepository | None = None,
    ) -> None:
        self.validator = validator
        self.executor = executor
        self.planner = planner
        self.dataset_repository = dataset_repository

    def validate(self, request: QueryRequest) -> bool:
        """Validate a query request against security and AST syntax rules."""
        self.validator.validate(request)
        return True

    def execute(self, request: QueryRequest) -> QueryResult:
        """Validate and execute a query request, returning tabular results."""
        self.validator.validate(request)
        return self.executor.execute(request)

    def explain(self, request: QueryRequest) -> QueryMetadata:
        """Validate and generate query execution plan metadata."""
        self.validator.validate(request)
        return self.planner.plan(request)

    def preview_dataset(
        self,
        dataset_id: str,
        limit: int = 10,
        offset: int = 0,
        parameters: dict[str, Any] | None = None,
    ) -> QueryResult:
        """Generate and execute a preview query for a specified dataset entity."""
        if self.dataset_repository is None:
            raise EntityNotFoundError("DatasetRepository", "not configured")

        dataset = self.dataset_repository.get_by_id(dataset_id)
        if not dataset:
            raise EntityNotFoundError("Dataset", dataset_id)

        # Build SQL query string from dataset classification
        if dataset.object_type == DatasetObjectType.QUERY and dataset.sql_query:
            sql_query = dataset.sql_query
        elif dataset.object_name:
            # Quote object name safely to prevent identifier injection
            safe_name = dataset.object_name.replace('"', '""')
            sql_query = f'SELECT * FROM "{safe_name}"'
        elif dataset.query_or_table:
            qt = dataset.query_or_table.strip()
            if qt.upper().startswith("SELECT") or qt.upper().startswith("WITH"):
                sql_query = qt
            else:
                safe_name = qt.replace('"', '""')
                sql_query = f'SELECT * FROM "{safe_name}"'
        else:
            raise EntityNotFoundError("Dataset query/table", dataset_id)

        request = QueryRequest.create(
            sql=sql_query,
            parameters=parameters or {},
            limit=limit,
            offset=offset,
            dataset_id=dataset_id,
        )

        return self.execute(request)
