from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.roles import router as roles_router
from app.api.v1.routers.users import router as users_router

__all__ = ["auth_router", "health_router", "roles_router", "users_router"]
