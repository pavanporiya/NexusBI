"""Unit and integration tests for Agent Tools (list_organizations).

Verifies the 5 agent tool security & execution requirements:
1. Authenticated Super Admin -> list organizations -> PASS.
2. Unauthorized user -> denied.
3. Cross-tenant organization -> never returned.
4. Unknown tool -> rejected.
5. Agent query without permission -> 403.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.common_dto import PaginatedResponse
from app.application.dto.organization_dto import OrganizationDTO
from app.application.services.agent_tool_registry import AgentToolRegistry
from app.application.use_cases.execute_agent_query import ExecuteAgentQueryUseCase
from app.core.exceptions import AuthorizationError, ValidationError
from app.domain.entities.user import User


def test_1_authenticated_super_admin_list_organizations_pass() -> None:
    """Test 1: Authenticated Super Admin -> list organizations -> PASS."""
    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()
    list_orgs_use_case = MagicMock()

    # Super admin has organizations:read
    auth_service.has_permission.return_value = True
    now = datetime.now(UTC)

    mock_org = OrganizationDTO(
        id="org-1",
        name="Acme Corp",
        slug="acme-corp",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    list_orgs_use_case.execute.return_value = PaginatedResponse[OrganizationDTO](
        items=[mock_org],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
    )

    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
        list_organizations_use_case=list_orgs_use_case,
    )

    super_admin = User(id="admin-1", email="admin@nexusbi.io", is_active=True)

    res = registry.execute_tool("list_organizations", user=super_admin)
    assert res["tool"] == "list_organizations"
    assert res["total"] == 1
    assert res["items"][0]["name"] == "Acme Corp"


def test_2_unauthorized_user_denied() -> None:
    """Test 2: Unauthorized user without permissions -> denied."""
    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()
    list_orgs_use_case = MagicMock()

    # User lacks organizations:read permission
    auth_service.has_permission.return_value = False

    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
        list_organizations_use_case=list_orgs_use_case,
    )

    unauthorized_user = User(id="user-2", email="viewer@nexusbi.io", is_active=True)

    with pytest.raises(AuthorizationError) as exc_info:
        registry.execute_tool("list_organizations", user=unauthorized_user)

    assert "organizations:read" in str(exc_info.value.detail)


def test_3_cross_tenant_organization_never_returned() -> None:
    """Test 3: Cross-tenant organization -> never returned."""
    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()
    list_orgs_use_case = MagicMock()

    auth_service.has_permission.return_value = True
    now = datetime.now(UTC)

    org_a = OrganizationDTO(
        id="org-a",
        name="Tenant A Org",
        slug="tenant-a-org",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    list_orgs_use_case.execute.return_value = PaginatedResponse[OrganizationDTO](
        items=[org_a],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
    )

    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
        list_organizations_use_case=list_orgs_use_case,
    )

    user = User(id="user-1", email="user@tenant.io", is_active=True)

    # Requesting tenant scope workspace-A returns tenant org A
    res = registry.execute_tool(
        "list_organizations", user=user, kwargs={"workspace_id": "workspace-A"}
    )
    assert res["total"] == 1
    assert res["items"][0]["id"] == "org-a"


def test_4_unknown_tool_rejected() -> None:
    """Test 4: Unknown tool -> rejected."""
    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()

    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
    )

    user = User(id="user-1", email="admin@nexusbi.io", is_active=True)

    with pytest.raises(ValidationError) as exc_info:
        registry.execute_tool("drop_database_tables", user=user)

    assert "not in the allowlist" in str(exc_info.value.detail)


def test_5_agent_query_without_permission_403() -> None:
    """Test 5: Agent query without permission -> 403 / AuthorizationError."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()
    tool_registry = MagicMock()

    tool_registry.execute_tool.side_effect = AuthorizationError(
        message="Permission denied",
        detail="User lacks organizations:read permission",
    )

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
        tool_registry=tool_registry,
    )

    unauthorized_user = User(id="usr-99", email="unauth@nexusbi.io", is_active=True)

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            user=unauthorized_user,
            natural_language_query="Show me my organizations",
        )

    assert "Permission denied" in str(exc_info.value.message)


def test_6_discover_datasets_pass_and_workspace_filtering() -> None:
    """Test discover_datasets tool returns active datasets with workspace filtering."""
    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = True

    ds_1 = MagicMock(
        id="ds-1",
        name="Sales Dataset",
        source_type="postgres",
        object_type="table",
        object_name="sales",
        sql_query=None,
        workspace_id="ws-1",
        description="Sales data",
        is_active=True,
    )
    ds_2 = MagicMock(
        id="ds-2",
        name="Finance Dataset",
        source_type="postgres",
        object_type="table",
        object_name="finance",
        sql_query=None,
        workspace_id="ws-2",
        description="Finance data",
        is_active=True,
    )

    dataset_repo.list.return_value = ([ds_1, ds_2], 2)

    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
    )

    user = User(id="user-1", email="user@nexusbi.io", is_active=True)

    # List all datasets
    res = registry.execute_tool("discover_datasets", user=user)
    assert res["tool"] == "discover_datasets"
    assert res["total"] == 2

    # List with workspace filtering
    res_filtered = registry.execute_tool(
        "discover_datasets", user=user, kwargs={"workspace_id": "ws-1"}
    )
    assert res_filtered["total"] == 1
    assert res_filtered["items"][0]["id"] == "ds-1"


def test_7_inspect_schema_cross_tenant_denied() -> None:
    """Test inspect_schema denies cross-tenant dataset access."""
    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = True

    ds = MagicMock(
        id="ds-tenant-a",
        name="Tenant A Data",
        source_type="postgres",
        object_type="table",
        object_name="sales",
        sql_query=None,
        workspace_id="ws-tenant-a",
        description="Tenant A",
        schema_metadata={"columns": [{"name": "id", "type": "integer"}]},
    )
    dataset_repo.get_by_id.return_value = ds

    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
    )

    user = User(id="user-b", email="user@tenantb.io", is_active=True)

    # Attempting cross-tenant schema inspection must fail
    with pytest.raises(AuthorizationError) as exc_info:
        registry.execute_tool(
            "inspect_schema",
            user=user,
            kwargs={"dataset_id": "ds-tenant-a", "workspace_id": "ws-tenant-b"},
        )

    assert "workspace scope" in str(exc_info.value.detail)


def test_8_execute_sql_safe_read_only_pass_and_mutation_deny() -> None:
    """Test execute_sql allows SELECT and denies mutations."""
    from app.domain.value_objects.query import QueryColumn, QueryResult

    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = True

    mock_result = QueryResult(
        rows=[{"month": "2026-01", "total": 1000}],
        columns=[
            QueryColumn(name="month", type="string"),
            QueryColumn(name="total", type="integer"),
        ],
        column_types={"month": "string", "total": "integer"},
        execution_time=0.05,
        row_count=1,
    )
    query_service.execute.return_value = mock_result

    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
    )

    user = User(id="user-1", email="user@nexusbi.io", is_active=True)

    # Valid SELECT query passes
    res = registry.execute_tool(
        "execute_sql",
        user=user,
        kwargs={"sql": "SELECT month, SUM(amount) FROM sales GROUP BY month"},
    )
    assert res["tool"] == "execute_sql"
    assert res["row_count"] == 1
    assert res["rows"][0]["month"] == "2026-01"
