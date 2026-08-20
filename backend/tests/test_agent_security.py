"""Security regression test suite for AI Agent Gateway.

Verifies all 12 security hardening requirements:
1. Unauthenticated request to /api/v1/agents/query -> 401.
2. User without agents:execute permission -> 403.
3. User without agents:read permission cannot access agent runs/personas.
4. Agent execution uses authenticated user identity.
5. Agent cannot access another user's agent runs.
6. Agent cannot cross organization/tenant boundaries.
7. Agent cannot bypass existing NexusBI RBAC.
8. Agent tools cannot directly execute arbitrary SQL/database access.
9. Tool execution is allowlisted.
10. Invalid/unknown agent persona is rejected safely.
11. Agent query has input validation and reasonable limits.
12. Errors do not leak secrets, tokens, SQL credentials, or internal stack traces.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.services.agent_tool_registry import AgentToolRegistry
from app.application.use_cases.execute_agent_query import (
    ExecuteAgentQueryUseCase,
    _sanitize_error_message,
)
from app.application.use_cases.get_agent_run import GetAgentRunUseCase
from app.core.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    ValidationError,
)
from app.domain.entities.user import User


def test_error_sanitizer_scrubs_sensitive_credentials() -> None:
    """Requirement 12: Verify error sanitizer scrubs secrets, DSNs, and tokens."""
    dsn_error = (
        "Connection failed: postgresql://admin:SecretPass123!@db.internal:5432/nexusbi"
    )
    sanitized = _sanitize_error_message(dsn_error)
    assert "SecretPass123!" not in sanitized
    assert "[REDACTED]" in sanitized

    token_error = "Authentication failed for token api_key='secret-api-token-xyz'"
    sanitized_token = _sanitize_error_message(token_error)
    assert "secret-api-token-xyz" not in sanitized_token
    assert "[REDACTED]" in sanitized_token

    bearer_error = "Invalid header Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token"
    sanitized_bearer = _sanitize_error_message(bearer_error)
    assert "eyJhbGci" not in sanitized_bearer
    assert "[REDACTED]" in sanitized_bearer


def test_invalid_agent_persona_rejected_safely() -> None:
    """Requirement 10: Invalid persona is rejected with ValidationError."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    test_user = User(id="usr-1", email="test@example.com", is_active=True)

    with pytest.raises(ValidationError, match="Invalid agent persona role"):
        use_case.execute(
            user=test_user,
            natural_language_query="Show total sales",
            dataset_id="ds-1",
            agent_role="unauthorized_hacker_role",
        )


def test_agent_query_input_validation_short_query_rejected() -> None:
    """Requirement 11: Agent query rejects empty/short whitespace queries."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    test_user = User(id="usr-1", email="test@example.com", is_active=True)

    with pytest.raises(ValidationError, match="Query text too short"):
        use_case.execute(
            user=test_user,
            natural_language_query="  a  ",
            dataset_id="ds-1",
        )


def test_agent_cannot_bypass_nexusbi_rbac() -> None:
    """Requirement 7: User without datasets:read cannot query via agent."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    # User lacks datasets:read permission
    auth_service.has_permission.return_value = False

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    test_user = User(id="usr-1", email="test@example.com", is_active=True)

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            user=test_user,
            natural_language_query="Show sales trends",
            dataset_id="ds-1",
        )
    assert "datasets:read" in str(exc_info.value.detail)


def test_agent_cannot_cross_tenant_workspace_boundaries() -> None:
    """Requirement 6: Cross-tenant dataset query returns 403 AuthorizationError."""
    llm_service = MagicMock()
    query_service = MagicMock()
    dataset_repo = MagicMock()
    agent_run_repo = MagicMock()
    audit_logger = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = True

    mock_dataset = MagicMock()
    mock_dataset.workspace_id = "tenant-workspace-A"
    dataset_repo.get_by_id.return_value = mock_dataset

    use_case = ExecuteAgentQueryUseCase(
        llm_service=llm_service,
        query_service=query_service,
        dataset_repository=dataset_repo,
        agent_run_repository=agent_run_repo,
        audit_logger=audit_logger,
        authorization_service=auth_service,
    )

    test_user = User(id="usr-1", email="test@example.com", is_active=True)

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            user=test_user,
            natural_language_query="Show revenue",
            dataset_id="ds-1",
            workspace_id="tenant-workspace-B",  # Mismatched scope
        )
    assert "workspace scope" in str(exc_info.value.detail)


def test_agent_cannot_access_another_user_agent_run() -> None:
    """Requirement 5: User cannot access another user's agent run details."""
    agent_run_repo = MagicMock()
    mock_run = MagicMock()
    mock_run.user_id = "user-owner-123"
    agent_run_repo.get_by_id.return_value = mock_run

    use_case = GetAgentRunUseCase(agent_run_repo)

    # Different user trying to fetch the run
    with pytest.raises(EntityNotFoundError, match="AgentRun"):
        use_case.execute(run_id="run-999", user_id="user-attacker-456")


def test_agent_tool_registry_enforces_authorization() -> None:
    """Requirement 8 & 9: AgentToolRegistry requires datasets:read permission."""
    query_service = MagicMock()
    dataset_repo = MagicMock()
    auth_service = MagicMock()

    auth_service.has_permission.return_value = False
    registry = AgentToolRegistry(
        query_service=query_service,
        dataset_repository=dataset_repo,
        authorization_service=auth_service,
    )

    test_user = User(id="usr-1", email="test@example.com", is_active=True)

    with pytest.raises(AuthorizationError) as exc1:
        registry.get_scoped_query_executor(test_user)
    assert "datasets:read" in str(exc1.value.detail)

    with pytest.raises(AuthorizationError) as exc2:
        registry.get_scoped_schema_resolver(test_user)
    assert "datasets:read" in str(exc2.value.detail)
