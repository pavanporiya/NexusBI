"""Infrastructure repositories package.

Exposes concrete SQLAlchemy-backed repository implementations.
"""

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
from app.infrastructure.repositories.workspace_repository import (
    SQLAlchemyWorkspaceRepository,
)

__all__ = [
    "SQLAlchemyDashboardRepository",
    "SQLAlchemyDatasetRepository",
    "SQLAlchemyMembershipRepository",
    "SQLAlchemyOrganizationRepository",
    "SQLAlchemyReportRepository",
    "SQLAlchemyRoleRepository",
    "SQLAlchemySessionRepository",
    "SQLAlchemyUserRepository",
    "SQLAlchemyWorkspaceRepository",
]
