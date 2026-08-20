"""Agent tool permission layer registry.

Wraps existing domain services in scoped tool adapters ensuring agents
only execute operations permitted to the authenticated user.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.application.services.interfaces import IAuthorizationService
from app.application.services.query_service import QueryService
from app.application.use_cases.list_organizations import ListOrganizationsUseCase
from app.core.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from app.domain.entities.user import User
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.value_objects.filter_params import FilterParams
from app.domain.value_objects.query import QueryRequest, QueryResult


class AgentToolRegistry:
    """Scoped registry for agent tool access and allowlisted execution."""

    ALLOWLISTED_TOOLS: set[str] = {
        "list_organizations",
        "discover_datasets",
        "inspect_schema",
        "execute_sql",
    }

    def __init__(
        self,
        *,
        query_service: QueryService,
        dataset_repository: IDatasetRepository,
        authorization_service: IAuthorizationService,
        list_organizations_use_case: ListOrganizationsUseCase | None = None,
    ) -> None:
        self._query_service = query_service
        self._dataset_repo = dataset_repository
        self._auth_service = authorization_service
        self._list_orgs_use_case = list_organizations_use_case

    def execute_tool(
        self,
        tool_name: str,
        *,
        user: User,
        kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an allowlisted agent tool enforcing RBAC and input validation.

        Parameters
        ----------
        tool_name : str
            Name of the tool to execute.
        user : User
            The authenticated user entity executing the tool.
        kwargs : dict[str, Any] | None
            Keyword arguments for the tool execution.

        Returns
        -------
        dict[str, Any]
            Structured result dictionary from the tool execution.

        Raises
        ------
        ValidationError
            If the tool is unknown or arguments fail validation.
        AuthorizationError
            If the user lacks required permission for the tool.
        """
        if tool_name not in self.ALLOWLISTED_TOOLS:
            raise ValidationError(
                message="Tool execution rejected",
                detail=f"Tool '{tool_name}' is not in the allowlist.",
            )

        tool_args = kwargs or {}

        if tool_name == "list_organizations":
            return self._execute_list_organizations(user=user, kwargs=tool_args)
        if tool_name == "discover_datasets":
            return self._execute_discover_datasets(user=user, kwargs=tool_args)
        if tool_name == "inspect_schema":
            return self._execute_inspect_schema(user=user, kwargs=tool_args)
        if tool_name == "execute_sql":
            return self._execute_sql(user=user, kwargs=tool_args)

        raise ValidationError(
            message="Tool execution rejected",
            detail=f"Tool '{tool_name}' handler not found.",
        )

    def _execute_list_organizations(
        self,
        *,
        user: User,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute list_organizations tool with RBAC check and tenant isolation."""
        if not self._auth_service.has_permission(user, "organizations:read"):
            raise AuthorizationError(
                message="Permission denied",
                detail=(
                    "User lacks organizations:read permission required for "
                    "list_organizations tool"
                ),
            )

        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 20)
        if not isinstance(page, int) or page < 1:
            raise ValidationError(
                message="Invalid pagination parameter",
                detail="page must be an integer >= 1",
            )
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise ValidationError(
                message="Invalid pagination parameter",
                detail="page_size must be an integer between 1 and 100",
            )

        if self._list_orgs_use_case is None:
            raise ValidationError(
                message="Tool service unavailable",
                detail="ListOrganizationsUseCase is not configured",
            )

        paginated_res = self._list_orgs_use_case.execute(page=page, page_size=page_size)

        target_workspace_id = kwargs.get("workspace_id")
        items = paginated_res.items

        if target_workspace_id:
            items = [
                org
                for org in items
                if not hasattr(org, "workspace_id")
                or org.workspace_id == target_workspace_id
            ]

        items_data = [
            item.model_dump() if hasattr(item, "model_dump") else (
                item.__dict__ if hasattr(item, "__dict__") else item
            )
            for item in items
        ]

        return {
            "tool": "list_organizations",
            "items": items_data,
            "total": len(items_data),
            "page": paginated_res.page,
            "page_size": paginated_res.page_size,
            "total_pages": paginated_res.total_pages,
        }

    def _execute_discover_datasets(
        self,
        *,
        user: User,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute discover_datasets tool with RBAC check and workspace isolation."""
        if not self._auth_service.has_permission(user, "datasets:read"):
            raise AuthorizationError(
                message="Permission denied",
                detail=(
                    "User lacks datasets:read permission required for "
                    "discover_datasets tool"
                ),
            )

        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 20)
        if not isinstance(page, int) or page < 1:
            raise ValidationError(
                message="Invalid pagination parameter",
                detail="page must be an integer >= 1",
            )
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise ValidationError(
                message="Invalid pagination parameter",
                detail="page_size must be an integer between 1 and 100",
            )

        target_workspace_id = kwargs.get("workspace_id")
        params = FilterParams(page=page, page_size=page_size, is_active=True)
        datasets, _total = self._dataset_repo.list(params)

        if target_workspace_id:
            datasets = [
                d
                for d in datasets
                if not getattr(d, "workspace_id", None)
                or d.workspace_id == target_workspace_id
            ]

        items_data = [
            {
                "id": d.id,
                "name": d.name,
                "source_type": str(d.source_type),
                "object_type": str(d.object_type),
                "object_name": d.object_name,
                "sql_query": d.sql_query,
                "workspace_id": getattr(d, "workspace_id", ""),
                "description": d.description,
                "is_active": d.is_active,
            }
            for d in datasets
        ]

        return {
            "tool": "discover_datasets",
            "items": items_data,
            "total": len(items_data),
            "page": page,
            "page_size": page_size,
        }

    def _execute_inspect_schema(
        self,
        *,
        user: User,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute inspect_schema tool with RBAC check and workspace boundary
        isolation.
        """
        if not self._auth_service.has_permission(user, "datasets:read"):
            raise AuthorizationError(
                message="Permission denied",
                detail=(
                    "User lacks datasets:read permission required for "
                    "inspect_schema tool"
                ),
            )

        dataset_id = kwargs.get("dataset_id")
        if not dataset_id or not isinstance(dataset_id, str):
            raise ValidationError(
                message="Invalid dataset_id parameter",
                detail="dataset_id must be a non-empty string",
            )

        dataset = self._dataset_repo.get_by_id(dataset_id)
        if dataset is None:
            raise EntityNotFoundError("Dataset", dataset_id)

        target_workspace_id = kwargs.get("workspace_id")
        ds_ws = getattr(dataset, "workspace_id", None)
        if target_workspace_id and ds_ws and ds_ws != target_workspace_id:
            raise AuthorizationError(
                message="Permission denied",
                detail="Dataset does not belong to the requested workspace scope",
            )

        return {
            "tool": "inspect_schema",
            "dataset_id": dataset.id,
            "name": dataset.name,
            "source_type": str(dataset.source_type),
            "object_type": str(dataset.object_type),
            "object_name": dataset.object_name,
            "sql_query": dataset.sql_query,
            "description": dataset.description,
            "workspace_id": getattr(dataset, "workspace_id", ""),
            "schema_metadata": dataset.schema_metadata,
        }

    def _execute_sql(
        self,
        *,
        user: User,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute safe read-only SQL tool enforcing RBAC, AST validation, and scope."""
        if not self._auth_service.has_permission(user, "datasets:read"):
            raise AuthorizationError(
                message="Permission denied",
                detail=(
                    "User lacks datasets:read permission required for "
                    "execute_sql tool"
                ),
            )

        sql = kwargs.get("sql")
        if not sql or not isinstance(sql, str) or not sql.strip():
            raise ValidationError(
                message="Invalid SQL parameter",
                detail="sql parameter must be a non-empty string",
            )

        dataset_id = kwargs.get("dataset_id")
        target_workspace_id = kwargs.get("workspace_id")

        if dataset_id:
            dataset = self._dataset_repo.get_by_id(dataset_id)
            if dataset is None:
                raise EntityNotFoundError("Dataset", dataset_id)
            ds_ws = getattr(dataset, "workspace_id", None)
            if target_workspace_id and ds_ws and ds_ws != target_workspace_id:
                raise AuthorizationError(
                    message="Permission denied",
                    detail="Dataset does not belong to the requested workspace scope",
                )

        parameters = kwargs.get("parameters") or {}
        limit = kwargs.get("limit", 100)
        offset = kwargs.get("offset", 0)

        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            limit = 100

        req = QueryRequest.create(
            sql=sql,
            parameters=parameters,
            limit=limit,
            offset=offset,
            dataset_id=dataset_id,
        )

        res = self._query_service.execute(req)

        return {
            "tool": "execute_sql",
            "rows": res.rows,
            "columns": [
                c.name if hasattr(c, "name") else str(c)
                for c in res.columns
            ],
            "column_types": res.column_types,
            "row_count": res.row_count,
            "execution_time_ms": res.execution_time * 1000,
        }

    def get_scoped_query_executor(
        self, user: User
    ) -> Callable[[QueryRequest], QueryResult]:
        """Return a query execution function bound to user authorization."""
        if not self._auth_service.has_permission(user, "datasets:read"):
            raise AuthorizationError(
                message="Permission denied",
                detail="User lacks datasets:read permission",
            )

        def executor(request: QueryRequest) -> QueryResult:
            return self._query_service.execute(request)

        return executor

    def get_scoped_schema_resolver(self, user: User) -> Callable[[str], Any]:
        """Return a dataset schema lookup function bound to user authorization."""
        if not self._auth_service.has_permission(user, "datasets:read"):
            raise AuthorizationError(
                message="Permission denied",
                detail="User lacks datasets:read permission",
            )

        def resolver(dataset_id: str) -> Any:
            return self._dataset_repo.get_by_id(dataset_id)

        return resolver

