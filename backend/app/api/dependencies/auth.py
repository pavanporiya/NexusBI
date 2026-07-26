"""Authentication FastAPI dependencies.

Provides reusable dependency functions for resolving the current authenticated
user entity using Clean Architecture use cases and repositories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.services import QueryService
from app.application.services.interfaces import (
    IAuthorizationService,
    IPasswordHasher,
    ITokenService,
)
from app.application.use_cases import (
    AddMemberUseCase,
    CreateDashboardUseCase,
    CreateDatasetUseCase,
    CreateOrganizationUseCase,
    CreateReportUseCase,
    CreateRoleUseCase,
    CreateWidgetUseCase,
    CreateWorkspaceUseCase,
    DeleteDashboardUseCase,
    DeleteDatasetUseCase,
    DeleteOrganizationUseCase,
    DeleteReportUseCase,
    DeleteRoleUseCase,
    DeleteWidgetUseCase,
    DeleteWorkspaceUseCase,
    GetCurrentUserUseCase,
    GetDashboardUseCase,
    GetDatasetUseCase,
    GetOrganizationUseCase,
    GetReportUseCase,
    GetRoleByIdUseCase,
    GetRolesUseCase,
    GetUserUseCase,
    GetWidgetUseCase,
    GetWorkspaceUseCase,
    ListDashboardsUseCase,
    ListDatasetsUseCase,
    ListMembersUseCase,
    ListOrganizationsUseCase,
    ListReportsUseCase,
    ListWidgetsUseCase,
    ListWorkspacesUseCase,
    LoginUserUseCase,
    LogoutUserUseCase,
    MoveWidgetUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
    RemoveMemberUseCase,
    ResizeWidgetUseCase,
    ToggleVisibilityUseCase,
    UpdateDashboardUseCase,
    UpdateDatasetUseCase,
    UpdateMemberRoleUseCase,
    UpdateOrganizationUseCase,
    UpdateReportUseCase,
    UpdateRoleUseCase,
    UpdateUserUseCase,
    UpdateWidgetUseCase,
    UpdateWorkspaceUseCase,
)
from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.exceptions import AuthenticationError
from app.domain.entities.user import User
from app.domain.repositories.dashboard_repository import IDashboardRepository
from app.domain.repositories.dataset_repository import IDatasetRepository
from app.domain.repositories.membership_repository import IMembershipRepository
from app.domain.repositories.organization_repository import IOrganizationRepository
from app.domain.repositories.report_repository import IReportRepository
from app.domain.repositories.role_repository import IRoleRepository
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.widget_repository import IWidgetRepository
from app.domain.repositories.workspace_repository import IWorkspaceRepository
from app.infrastructure.repositories.dashboard_repository import (
    SQLAlchemyDashboardRepository,
)
from app.infrastructure.repositories.dataset_repository import (
    SQLAlchemyDatasetRepository,
)
from app.infrastructure.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)
from app.infrastructure.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
)
from app.infrastructure.repositories.report_repository import (
    SQLAlchemyReportRepository,
)
from app.infrastructure.repositories.role_repository import (
    SQLAlchemyRoleRepository,
)
from app.infrastructure.repositories.session_repository import (
    SQLAlchemySessionRepository,
)
from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from app.infrastructure.repositories.widget_repository import (
    SQLAlchemyWidgetRepository,
)
from app.infrastructure.repositories.workspace_repository import (
    SQLAlchemyWorkspaceRepository,
)
from app.infrastructure.services.authorization_service import AuthorizationService
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.services.jwt_token_service import JWTTokenService

if TYPE_CHECKING:
    from app.application.services.chart_service import ChartService

security = HTTPBearer(auto_error=False)


def get_token_service() -> ITokenService:
    """Dependency provider for ITokenService."""
    settings = get_settings()
    return JWTTokenService(
        secret_key=settings.SECRET_KEY.get_secret_value(),
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_password_hasher() -> IPasswordHasher:
    """Dependency provider for IPasswordHasher."""
    return BcryptPasswordHasher()


def get_user_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IUserRepository:
    """Dependency provider for IUserRepository."""
    return SQLAlchemyUserRepository(db)


def get_session_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ISessionRepository:
    """Dependency provider for ISessionRepository."""
    return SQLAlchemySessionRepository(db)


def get_role_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IRoleRepository:
    """Dependency provider for IRoleRepository."""
    return SQLAlchemyRoleRepository(db)


def get_authorization_service() -> IAuthorizationService:
    """Dependency provider for IAuthorizationService."""
    return AuthorizationService()


def get_register_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
) -> RegisterUserUseCase:
    """Dependency provider for RegisterUserUseCase."""
    return RegisterUserUseCase(
        user_repository=user_repo,
        password_hasher=password_hasher,
    )


def get_login_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    session_repo: Annotated[ISessionRepository, Depends(get_session_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> LoginUserUseCase:
    """Dependency provider for LoginUserUseCase."""
    return LoginUserUseCase(
        user_repository=user_repo,
        session_repository=session_repo,
        password_hasher=password_hasher,
        token_service=token_service,
    )


def get_refresh_token_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    session_repo: Annotated[ISessionRepository, Depends(get_session_repository)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> RefreshTokenUseCase:
    """Dependency provider for RefreshTokenUseCase."""
    return RefreshTokenUseCase(
        user_repository=user_repo,
        session_repository=session_repo,
        token_service=token_service,
    )


def get_logout_user_use_case(
    session_repo: Annotated[ISessionRepository, Depends(get_session_repository)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> LogoutUserUseCase:
    """Dependency provider for LogoutUserUseCase."""
    return LogoutUserUseCase(
        session_repository=session_repo,
        token_service=token_service,
    )


def get_current_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> GetCurrentUserUseCase:
    """Dependency provider for GetCurrentUserUseCase."""
    return GetCurrentUserUseCase(
        user_repository=user_repo,
        token_service=token_service,
    )


def get_get_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> GetUserUseCase:
    """Dependency provider for GetUserUseCase."""
    return GetUserUseCase(user_repository=user_repo)


def get_update_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UpdateUserUseCase:
    """Dependency provider for UpdateUserUseCase."""
    return UpdateUserUseCase(user_repository=user_repo)


def get_get_roles_use_case(
    role_repo: Annotated[IRoleRepository, Depends(get_role_repository)],
) -> GetRolesUseCase:
    """Dependency provider for GetRolesUseCase."""
    return GetRolesUseCase(role_repository=role_repo)


def get_get_role_by_id_use_case(
    role_repo: Annotated[IRoleRepository, Depends(get_role_repository)],
) -> GetRoleByIdUseCase:
    """Dependency provider for GetRoleByIdUseCase."""
    return GetRoleByIdUseCase(role_repository=role_repo)


def get_create_role_use_case(
    role_repo: Annotated[IRoleRepository, Depends(get_role_repository)],
) -> CreateRoleUseCase:
    """Dependency provider for CreateRoleUseCase."""
    return CreateRoleUseCase(role_repository=role_repo)


def get_update_role_use_case(
    role_repo: Annotated[IRoleRepository, Depends(get_role_repository)],
) -> UpdateRoleUseCase:
    """Dependency provider for UpdateRoleUseCase."""
    return UpdateRoleUseCase(role_repository=role_repo)


def get_delete_role_use_case(
    role_repo: Annotated[IRoleRepository, Depends(get_role_repository)],
) -> DeleteRoleUseCase:
    """Dependency provider for DeleteRoleUseCase."""
    return DeleteRoleUseCase(role_repository=role_repo)


# ---------------------------------------------------------------------------
# BI Foundation Repository Dependencies
# ---------------------------------------------------------------------------


def get_dashboard_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IDashboardRepository:
    """Dependency provider for IDashboardRepository."""
    return SQLAlchemyDashboardRepository(db)


def get_report_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IReportRepository:
    """Dependency provider for IReportRepository."""
    return SQLAlchemyReportRepository(db)


def get_dataset_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IDatasetRepository:
    """Dependency provider for IDatasetRepository."""
    return SQLAlchemyDatasetRepository(db)


# ---------------------------------------------------------------------------
# BI Foundation Use Case Dependencies
# ---------------------------------------------------------------------------


# Dashboard Use Cases
def get_create_dashboard_use_case(
    repo: Annotated[IDashboardRepository, Depends(get_dashboard_repository)],
    dataset_repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> CreateDashboardUseCase:
    """Dependency provider for CreateDashboardUseCase."""
    return CreateDashboardUseCase(
        dashboard_repository=repo, dataset_repository=dataset_repo
    )


def get_get_dashboard_use_case(
    repo: Annotated[IDashboardRepository, Depends(get_dashboard_repository)],
) -> GetDashboardUseCase:
    """Dependency provider for GetDashboardUseCase."""
    return GetDashboardUseCase(dashboard_repository=repo)


def get_update_dashboard_use_case(
    repo: Annotated[IDashboardRepository, Depends(get_dashboard_repository)],
    dataset_repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> UpdateDashboardUseCase:
    """Dependency provider for UpdateDashboardUseCase."""
    return UpdateDashboardUseCase(
        dashboard_repository=repo, dataset_repository=dataset_repo
    )


def get_delete_dashboard_use_case(
    repo: Annotated[IDashboardRepository, Depends(get_dashboard_repository)],
) -> DeleteDashboardUseCase:
    """Dependency provider for DeleteDashboardUseCase."""
    return DeleteDashboardUseCase(dashboard_repository=repo)


def get_list_dashboards_use_case(
    repo: Annotated[IDashboardRepository, Depends(get_dashboard_repository)],
) -> ListDashboardsUseCase:
    """Dependency provider for ListDashboardsUseCase."""
    return ListDashboardsUseCase(dashboard_repository=repo)


# Report Use Cases
def get_create_report_use_case(
    repo: Annotated[IReportRepository, Depends(get_report_repository)],
    dataset_repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> CreateReportUseCase:
    """Dependency provider for CreateReportUseCase."""
    return CreateReportUseCase(report_repository=repo, dataset_repository=dataset_repo)


def get_get_report_use_case(
    repo: Annotated[IReportRepository, Depends(get_report_repository)],
) -> GetReportUseCase:
    """Dependency provider for GetReportUseCase."""
    return GetReportUseCase(report_repository=repo)


def get_update_report_use_case(
    repo: Annotated[IReportRepository, Depends(get_report_repository)],
    dataset_repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> UpdateReportUseCase:
    """Dependency provider for UpdateReportUseCase."""
    return UpdateReportUseCase(report_repository=repo, dataset_repository=dataset_repo)


def get_delete_report_use_case(
    repo: Annotated[IReportRepository, Depends(get_report_repository)],
) -> DeleteReportUseCase:
    """Dependency provider for DeleteReportUseCase."""
    return DeleteReportUseCase(report_repository=repo)


def get_list_reports_use_case(
    repo: Annotated[IReportRepository, Depends(get_report_repository)],
) -> ListReportsUseCase:
    """Dependency provider for ListReportsUseCase."""
    return ListReportsUseCase(report_repository=repo)


# Dataset Use Cases
def get_create_dataset_use_case(
    repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> CreateDatasetUseCase:
    """Dependency provider for CreateDatasetUseCase."""
    return CreateDatasetUseCase(dataset_repository=repo)


def get_get_dataset_use_case(
    repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> GetDatasetUseCase:
    """Dependency provider for GetDatasetUseCase."""
    return GetDatasetUseCase(dataset_repository=repo)


def get_update_dataset_use_case(
    repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> UpdateDatasetUseCase:
    """Dependency provider for UpdateDatasetUseCase."""
    return UpdateDatasetUseCase(dataset_repository=repo)


def get_delete_dataset_use_case(
    repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> DeleteDatasetUseCase:
    """Dependency provider for DeleteDatasetUseCase."""
    return DeleteDatasetUseCase(dataset_repository=repo)


def get_list_datasets_use_case(
    repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> ListDatasetsUseCase:
    """Dependency provider for ListDatasetsUseCase."""
    return ListDatasetsUseCase(dataset_repository=repo)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    use_case: Annotated[GetCurrentUserUseCase, Depends(get_current_user_use_case)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> User:
    """FastAPI dependency that resolves the authenticated User domain entity.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials | None
        Bearer token credentials extracted from the Authorization header.
    use_case : GetCurrentUserUseCase
        Use case orchestrator for token decoding and verification.
    user_repo : IUserRepository
        Repository interface used to load the rich User domain entity.

    Returns
    -------
    User
        The authenticated active User domain entity.

    Raises
    ------
    AuthenticationError
        If authorization credentials are missing or the token/user is invalid.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError(
            "Not authenticated", detail="Missing authorization header"
        )

    token = credentials.credentials
    user_dto = use_case.execute(token)

    user = user_repo.get_by_id(user_dto.id)
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return user


# ---------------------------------------------------------------------------
# Organization Dependencies
# ---------------------------------------------------------------------------


def get_organization_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IOrganizationRepository:
    """Dependency provider for IOrganizationRepository."""
    return SQLAlchemyOrganizationRepository(db)


def get_create_organization_use_case(
    org_repo: Annotated[IOrganizationRepository, Depends(get_organization_repository)],
) -> CreateOrganizationUseCase:
    """Dependency provider for CreateOrganizationUseCase."""
    return CreateOrganizationUseCase(org_repo)


def get_update_organization_use_case(
    org_repo: Annotated[IOrganizationRepository, Depends(get_organization_repository)],
) -> UpdateOrganizationUseCase:
    """Dependency provider for UpdateOrganizationUseCase."""
    return UpdateOrganizationUseCase(org_repo)


def get_delete_organization_use_case(
    org_repo: Annotated[IOrganizationRepository, Depends(get_organization_repository)],
) -> DeleteOrganizationUseCase:
    """Dependency provider for DeleteOrganizationUseCase."""
    return DeleteOrganizationUseCase(org_repo)


def get_get_organization_use_case(
    org_repo: Annotated[IOrganizationRepository, Depends(get_organization_repository)],
) -> GetOrganizationUseCase:
    """Dependency provider for GetOrganizationUseCase."""
    return GetOrganizationUseCase(org_repo)


def get_list_organizations_use_case(
    org_repo: Annotated[IOrganizationRepository, Depends(get_organization_repository)],
) -> ListOrganizationsUseCase:
    """Dependency provider for ListOrganizationsUseCase."""
    return ListOrganizationsUseCase(org_repo)


# ---------------------------------------------------------------------------
# Workspace Dependencies
# ---------------------------------------------------------------------------


def get_workspace_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IWorkspaceRepository:
    """Dependency provider for IWorkspaceRepository."""
    return SQLAlchemyWorkspaceRepository(db)


def get_create_workspace_use_case(
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
    organization_repo: Annotated[
        IOrganizationRepository, Depends(get_organization_repository)
    ],
) -> CreateWorkspaceUseCase:
    """Dependency provider for CreateWorkspaceUseCase."""
    return CreateWorkspaceUseCase(workspace_repo, organization_repo)


def get_update_workspace_use_case(
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
) -> UpdateWorkspaceUseCase:
    """Dependency provider for UpdateWorkspaceUseCase."""
    return UpdateWorkspaceUseCase(workspace_repo)


def get_delete_workspace_use_case(
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
) -> DeleteWorkspaceUseCase:
    """Dependency provider for DeleteWorkspaceUseCase."""
    return DeleteWorkspaceUseCase(workspace_repo)


def get_get_workspace_use_case(
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
) -> GetWorkspaceUseCase:
    """Dependency provider for GetWorkspaceUseCase."""
    return GetWorkspaceUseCase(workspace_repo)


def get_list_workspaces_use_case(
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
) -> ListWorkspacesUseCase:
    """Dependency provider for ListWorkspacesUseCase."""
    return ListWorkspacesUseCase(workspace_repo)


# ---------------------------------------------------------------------------
# Membership Dependencies
# ---------------------------------------------------------------------------


def get_membership_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IMembershipRepository:
    """Dependency provider for IMembershipRepository."""
    return SQLAlchemyMembershipRepository(db)


def get_add_member_use_case(
    membership_repo: Annotated[
        IMembershipRepository, Depends(get_membership_repository)
    ],
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    role_repo: Annotated[IRoleRepository, Depends(get_role_repository)],
) -> AddMemberUseCase:
    """Dependency provider for AddMemberUseCase."""
    return AddMemberUseCase(membership_repo, workspace_repo, user_repo, role_repo)


def get_remove_member_use_case(
    membership_repo: Annotated[
        IMembershipRepository, Depends(get_membership_repository)
    ],
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
) -> RemoveMemberUseCase:
    """Dependency provider for RemoveMemberUseCase."""
    return RemoveMemberUseCase(membership_repo, workspace_repo)


def get_update_member_role_use_case(
    membership_repo: Annotated[
        IMembershipRepository, Depends(get_membership_repository)
    ],
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
    role_repo: Annotated[IRoleRepository, Depends(get_role_repository)],
) -> UpdateMemberRoleUseCase:
    """Dependency provider for UpdateMemberRoleUseCase."""
    return UpdateMemberRoleUseCase(membership_repo, workspace_repo, role_repo)


def get_list_members_use_case(
    membership_repo: Annotated[
        IMembershipRepository, Depends(get_membership_repository)
    ],
    workspace_repo: Annotated[IWorkspaceRepository, Depends(get_workspace_repository)],
) -> ListMembersUseCase:
    """Dependency provider for ListMembersUseCase."""
    return ListMembersUseCase(membership_repo, workspace_repo)


# ---------------------------------------------------------------------------
# Widget Dependencies
# ---------------------------------------------------------------------------


def get_widget_repository(
    db: Annotated[Session, Depends(get_db)],
) -> IWidgetRepository:
    """Dependency provider for IWidgetRepository."""
    return SQLAlchemyWidgetRepository(db)


def get_create_widget_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
    dashboard_repo: Annotated[IDashboardRepository, Depends(get_dashboard_repository)],
    dataset_repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> CreateWidgetUseCase:
    """Dependency provider for CreateWidgetUseCase."""
    return CreateWidgetUseCase(widget_repo, dashboard_repo, dataset_repo)


def get_get_widget_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
) -> GetWidgetUseCase:
    """Dependency provider for GetWidgetUseCase."""
    return GetWidgetUseCase(widget_repo)


def get_update_widget_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
    dataset_repo: Annotated[IDatasetRepository, Depends(get_dataset_repository)],
) -> UpdateWidgetUseCase:
    """Dependency provider for UpdateWidgetUseCase."""
    return UpdateWidgetUseCase(widget_repo, dataset_repo)


def get_delete_widget_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
) -> DeleteWidgetUseCase:
    """Dependency provider for DeleteWidgetUseCase."""
    return DeleteWidgetUseCase(widget_repo)


def get_list_widgets_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
    dashboard_repo: Annotated[IDashboardRepository, Depends(get_dashboard_repository)],
) -> ListWidgetsUseCase:
    """Dependency provider for ListWidgetsUseCase."""
    return ListWidgetsUseCase(widget_repo, dashboard_repo)


def get_move_widget_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
) -> MoveWidgetUseCase:
    """Dependency provider for MoveWidgetUseCase."""
    return MoveWidgetUseCase(widget_repo)


def get_resize_widget_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
) -> ResizeWidgetUseCase:
    """Dependency provider for ResizeWidgetUseCase."""
    return ResizeWidgetUseCase(widget_repo)


def get_toggle_visibility_use_case(
    widget_repo: Annotated[IWidgetRepository, Depends(get_widget_repository)],
) -> ToggleVisibilityUseCase:
    """Dependency provider for ToggleVisibilityUseCase."""
    return ToggleVisibilityUseCase(widget_repo)


def get_query_service(
    db: Annotated[Session, Depends(get_db)],
) -> QueryService:
    """Dependency provider for QueryService."""
    from app.infrastructure.query.sqlalchemy_executor import (
        SqlAlchemyQueryExecutor,
    )
    from app.infrastructure.query.sqlalchemy_planner import (
        SqlAlchemyQueryPlanner,
    )
    from app.infrastructure.query.sqlalchemy_validator import (
        SqlAlchemyQueryValidator,
    )
    from app.infrastructure.repositories.dataset_repository import (
        SQLAlchemyDatasetRepository,
    )

    engine = db.get_bind()
    validator = SqlAlchemyQueryValidator()
    executor = SqlAlchemyQueryExecutor(engine=engine)
    planner = SqlAlchemyQueryPlanner(engine=engine)
    dataset_repo = SQLAlchemyDatasetRepository(db)
    return QueryService(
        validator=validator,
        executor=executor,
        planner=planner,
        dataset_repository=dataset_repo,
    )


def get_chart_service() -> ChartService:
    """Dependency provider for ChartService."""
    from app.application.services.chart_service import ChartService

    return ChartService()
