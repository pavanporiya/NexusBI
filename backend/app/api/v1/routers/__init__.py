from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.charts import router as charts_router
from app.api.v1.routers.dashboards import router as dashboards_router
from app.api.v1.routers.datasets import router as datasets_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.organizations import router as organizations_router
from app.api.v1.routers.query import router as query_router
from app.api.v1.routers.reports import router as reports_router
from app.api.v1.routers.roles import router as roles_router
from app.api.v1.routers.users import router as users_router
from app.api.v1.routers.widgets import router as widgets_router
from app.api.v1.routers.workspaces import router as workspaces_router

__all__ = [
    "auth_router",
    "charts_router",
    "dashboards_router",
    "datasets_router",
    "health_router",
    "organizations_router",
    "query_router",
    "reports_router",
    "roles_router",
    "users_router",
    "widgets_router",
    "workspaces_router",
]
